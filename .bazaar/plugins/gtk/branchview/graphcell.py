# -*- coding: UTF-8 -*-
"""Cell renderer for directed graph.

This module contains the implementation of a custom GtkCellRenderer that
draws part of the directed graph based on the lines suggested by the code
in graph.py.

Because we're shiny, we use Cairo to do this, and because we're naughty
we cheat and draw over the bits of the TreeViewColumn that are supposed to
just be for the background.
"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"


import math

import gtk
import gobject
import pango
import cairo


class CellRendererGraph(gtk.GenericCellRenderer):
    """Cell renderer for directed graph.

    Properties:
      node              (column, colour) tuple to draw revision node,
      in_lines          (start, end, colour) tuple list to draw inward lines,
      out_lines         (start, end, colour) tuple list to draw outward lines.
    """
    
    columns_len = 0

    __gproperties__ = {
        "node":         ( gobject.TYPE_PYOBJECT, "node",
                          "revision node instruction",
                          gobject.PARAM_WRITABLE
                        ),
        "tags":         ( gobject.TYPE_PYOBJECT, "tags",
                          "list of tags associated with the node",
                          gobject.PARAM_WRITABLE
                        ),
        "in-lines":     ( gobject.TYPE_PYOBJECT, "in-lines",
                          "instructions to draw lines into the cell",
                          gobject.PARAM_WRITABLE
                        ),
        "out-lines":    ( gobject.TYPE_PYOBJECT, "out-lines",
                          "instructions to draw lines out of the cell",
                          gobject.PARAM_WRITABLE
                        ),
        }
    
    def do_set_property(self, property, value):
        """Set properties from GObject properties."""
        if property.name == "node":
            self.node = value
        elif property.name == "tags":
            self.tags = value
        elif property.name == "in-lines":
            self.in_lines = value
        elif property.name == "out-lines":
            self.out_lines = value
        else:
            raise AttributeError, "no such property: '%s'" % property.name

    def box_size(self, widget):
        """Calculate box size based on widget's font.

        Cache this as it's probably expensive to get.  It ensures that we
        draw the graph at least as large as the text.
        """
        try:
            return self._box_size
        except AttributeError:
            pango_ctx = widget.get_pango_context()
            font_desc = widget.get_style().font_desc
            metrics = pango_ctx.get_metrics(font_desc)

            ascent = pango.PIXELS(metrics.get_ascent())
            descent = pango.PIXELS(metrics.get_descent())

            self._box_size = ascent + descent + 6
            return self._box_size

    def set_colour(self, ctx, colour, bg, fg):
        """Set the context source colour.

        Picks a distinct colour based on an internal wheel; the bg
        parameter provides the value that should be assigned to the 'zero'
        colours and the fg parameter provides the multiplier that should be
        applied to the foreground colours.
        """
        mainline_color = ( 0.0, 0.0, 0.0 )
        colours = [
            ( 1.0, 0.0, 0.0 ),
            ( 1.0, 1.0, 0.0 ),
            ( 0.0, 1.0, 0.0 ),
            ( 0.0, 1.0, 1.0 ),
            ( 0.0, 0.0, 1.0 ),
            ( 1.0, 0.0, 1.0 ),
            ]

        if colour == 0:
            colour_rgb = mainline_color
        else:
            colour_rgb = colours[colour % len(colours)]

        red   = (colour_rgb[0] * fg) or bg
        green = (colour_rgb[1] * fg) or bg
        blue  = (colour_rgb[2] * fg) or bg

        ctx.set_source_rgb(red, green, blue)

    def on_get_size(self, widget, cell_area):
        """Return the size we need for this cell.

        Each cell is drawn individually and is only as wide as it needs
        to be, we let the TreeViewColumn take care of making them all
        line up.
        """
        box_size = self.box_size(widget) + 1

        width = box_size * (self.columns_len + 1)
        height = box_size

        # FIXME I have no idea how to use cell_area properly
        return (0, 0, width, height)

    def on_render(self, window, widget, bg_area, cell_area, exp_area, flags):
        """Render an individual cell.

        Draws the cell contents using cairo, taking care to clip what we
        do to within the background area so we don't draw over other cells.
        Note that we're a bit naughty there and should really be drawing
        in the cell_area (or even the exposed area), but we explicitly don't
        want any gutter.

        We try and be a little clever, if the line we need to draw is going
        to cross other columns we actually draw it as in the .---' style
        instead of a pure diagonal ... this reduces confusion by an
        incredible amount.
        """
        ctx = window.cairo_create()
        ctx.rectangle(bg_area.x, bg_area.y, bg_area.width, bg_area.height)
        ctx.clip()

        box_size = self.box_size(widget)

        ctx.set_line_width(box_size / 8)

        # Draw lines into the cell
        for start, end, colour in self.in_lines:
            self.render_line (ctx, cell_area, box_size,
                         bg_area.y, bg_area.height,
                         start, end, colour, flags)

        # Draw lines out of the cell
        for start, end, colour in self.out_lines:
            self.render_line (ctx, cell_area, box_size,
                         bg_area.y + bg_area.height, bg_area.height,
                         start, end, colour, flags)

        # Draw the revision node in the right column
        (column, colour) = self.node
        ctx.arc(cell_area.x + box_size * column + box_size / 2,
                cell_area.y + cell_area.height / 2,
                box_size / 4, 0, 2 * math.pi)

        if flags & gtk.CELL_RENDERER_SELECTED:
            ctx.set_source_rgb(1.0, 1.0, 1.0)
            ctx.set_line_width(box_size / 4)
            ctx.stroke_preserve()
            ctx.set_line_width(box_size / 8)

        self.set_colour(ctx, colour, 0.0, 0.5)
        ctx.stroke_preserve()

        self.set_colour(ctx, colour, 0.5, 1.0)
        ctx.fill()

        self.render_tags(ctx, widget.create_pango_context(), cell_area, box_size)
    
    def render_line(self, ctx, cell_area, box_size, mid, height, start, end, colour, flags):
        if start is None:
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            x = cell_area.x + box_size * end + box_size / 2
            ctx.move_to(x, mid + height / 3)
            ctx.line_to(x, mid + height / 3)
            ctx.move_to(x, mid + height / 6)
            ctx.line_to(x, mid + height / 6)
            
        elif end is None:
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            x = cell_area.x + box_size * start + box_size / 2
            ctx.move_to(x, mid - height / 3)
            ctx.line_to(x, mid - height / 3)
            ctx.move_to(x, mid - height / 6)
            ctx.line_to(x, mid - height / 6)

        else:
            ctx.set_line_cap(cairo.LINE_CAP_BUTT)
            startx = cell_area.x + box_size * start + box_size / 2
            endx = cell_area.x + box_size * end + box_size / 2
            
            ctx.move_to(startx, mid - height / 2)
            
            if start - end == 0 :
                ctx.line_to(endx, mid + height / 2 + 1)
            else:
                ctx.curve_to(startx, mid - height / 5,
                             startx, mid - height / 5,
                             startx + (endx - startx) / 2, mid)

                ctx.curve_to(endx, mid + height / 5,
                             endx, mid + height / 5 ,
                             endx, mid + height / 2 + 1)

        if flags & gtk.CELL_RENDERER_SELECTED:
            ctx.set_source_rgb(1.0, 1.0, 1.0)
            ctx.set_line_width(box_size / 5)
            ctx.stroke_preserve()
            ctx.set_line_width(box_size / 8)

        self.set_colour(ctx, colour, 0.0, 0.65)

        ctx.stroke()

    def render_tags(self, ctx, pango_ctx, cell_area, box_size):
        # colour ID used in self.set_colour on the tags
        TAG_COLOUR_ID = 1

        (column, colour) = self.node

        font_desc = pango.FontDescription()
        font_desc.set_size(pango.SCALE * 7)

        tag_layout = pango.Layout(pango_ctx)
        tag_layout.set_font_description(font_desc)

        # The width of the tag label stack
        width = 0

        for tag_idx, tag in enumerate(self.tags):
            tag_layout.set_text(" " + tag + " ")
            text_width, text_height = tag_layout.get_pixel_size()

            x0 = cell_area.x + \
                 box_size * (column + 1.3) + width

            y0 = cell_area.y + \
                 cell_area.height / 2 - \
                 text_height / 2

            width += text_width + 5

            # Draw the tag border
            ctx.move_to(x0 - box_size / 3, y0 + text_height / 2)
            ctx.line_to(x0, y0)
            ctx.line_to(x0 + text_width, y0)
            ctx.line_to(x0 + text_width, y0 + text_height)
            ctx.line_to(x0, y0 + text_height)
            ctx.line_to(x0 - box_size / 3, y0 + text_height / 2)

            ctx.new_sub_path()
            ctx.arc(x0 - box_size / 12,
                        y0 + text_height / 2,
                        box_size / 7,
                        0, 2 * math.pi);

            self.set_colour(ctx, TAG_COLOUR_ID, 0.0, 0.5)
            ctx.stroke_preserve()

            ctx.set_fill_rule (cairo.FILL_RULE_EVEN_ODD)
            self.set_colour(ctx, TAG_COLOUR_ID, 0.5, 1.0)
            ctx.fill()

            # Draw the tag text
            self.set_colour(ctx, 0, 0.0, 0.0)
            ctx.move_to(x0, y0)
            ctx.show_layout(tag_layout)

