# Copyright (C) 2005 Dan Loda <danloda@gmail.com>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import pygtk
pygtk.require("2.0")
import gobject
import gtk


(
    SPAN_DAYS_COL,
    SPAN_STR_COL,
    SPAN_IS_SEPARATOR_COL,
    SPAN_IS_CUSTOM_COL
) = range(4)


class SpanSelector(gtk.HBox):
    """Encapsulates creation and functionality of widgets used for changing
    highlight spans.
    
    Note that calling any activate_* methods will emit "span-changed".
    """
    
    max_custom_spans = 4
    custom_spans = []
    last_selected = None

    def __init__(self, homogeneous=False, spacing=6):
        gtk.HBox.__init__(self, homogeneous, spacing)

        self.model = self._create_model()
        self.combo = self._create_combobox(self.model)
        self.entry = self._create_custom_entry()

        label = gtk.Label("Highlighting spans:")
        label.show()

        self.pack_start(label, expand=False, fill=True)
        self.pack_start(self.combo, expand=False, fill=False)
        self.pack_start(self.entry, expand=False, fill=False)

    def set_to_oldest_span(self, span):
        """Set the span associated with the "to Oldest Revision" entry."""
        self.model.set_value(self.oldest_iter, SPAN_DAYS_COL, span)

    def set_newest_to_oldest_span(self, span):
        """Set the span associated with the "Newest to Oldset" entry."""
        self.model.set_value(self.newest_iter, SPAN_DAYS_COL, span)

    def set_max_custom_spans(self, n):
        """Store up to n custom span entries in the combo box."""
        self.max_custom_spans = n

    def activate(self, iter):
        """Activate the row pointed to by gtk.TreeIter iter."""
        index = self._get_index_from_iter(iter)
        self.combo.set_active(index)

    def activate_last_selected(self):
        """Activate the previously selected row.

        Expected to be used when cancelling custom entry or revieved bad
        input.
        """
        if self.last_selected:
            self.activate(self.last_selected)

    def activate_default(self):
        """Activate the default row."""
        # TODO allow setting of default?
        self.activate(self.oldest_iter)

    def _get_index_from_iter(self, iter):
        """Returns a row index integer from iterator."""
        return int(self.model.get_string_from_iter(iter))

    def _combo_changed_cb(self, w):
        model = w.get_model()
        iter = w.get_active_iter()

        if model.get_value(iter, SPAN_IS_CUSTOM_COL):
            self._request_custom_span()
        else:
            self.last_selected = iter
            self.emit("span-changed", model.get_value(iter, SPAN_DAYS_COL))

    def _activate_custom_span_cb(self, w):
        self.entry.hide_all()
        self.combo.show()

        span = float(w.get_text())
        
        if span == 0:
            # FIXME this works as "cancel", returning to the previous span,
            # but it emits "span-changed", which isn't necessary.
            self.activate_last_selected()
            return

        self.add_custom_span(span)
        self.emit("custom-span-added", span)

        self.activate(self.custom_iter)

    def add_custom_span(self, span):
        if not len(self.custom_spans):
            self.custom_iter = self.model.insert_after(self.custom_iter,
                                                       self.separator)
            self.custom_iter_top = self.custom_iter.copy()
        
        if len(self.custom_spans) == self.max_custom_spans:
            self.custom_spans.pop(0)
            self.model.remove(self.model.iter_next(self.custom_iter_top))
        
        self.custom_spans.append(span)
        self.custom_iter = self.model.insert_after(
            self.custom_iter, [span, "%.2f Days" % span, False, False])

    def _request_custom_span(self):
        self.combo.hide()
        self.entry.show_all()

    def _create_model(self):
        # [span in days, span as string, row is seperator?, row is select
        # default?]
        m = gtk.ListStore(gobject.TYPE_FLOAT,
                          gobject.TYPE_STRING,
                          gobject.TYPE_BOOLEAN,
                          gobject.TYPE_BOOLEAN)

        self.separator = [0., "", True, False]
        
        self.oldest_iter = m.append([0., "to Oldest Revision", False, False])
        self.newest_iter = m.append([0., "Newest to Oldest", False, False])
        m.append(self.separator)
        m.append([1., "1 Day", False, False])
        m.append([7., "1 Week", False, False])
        m.append([30., "1 Month", False, False])
        self.custom_iter = m.append([365., "1 Year", False, False])
        m.append(self.separator)
        m.append([0., "Custom...", False, True])

        return m

    def _create_combobox(self, model):
        cb = gtk.ComboBox(model)
        cb.set_row_separator_func(
            lambda m, i: m.get_value(i, SPAN_IS_SEPARATOR_COL))
        cell = gtk.CellRendererText()
        cb.pack_start(cell, False)
        cb.add_attribute(cell, "text", SPAN_STR_COL)
        cb.connect("changed", self._combo_changed_cb)
        cb.show()

        return cb

    def _create_custom_entry(self):
        entry = gtk.HBox(False, 6)
        
        spin = gtk.SpinButton(digits=2)
        spin.set_numeric(True)
        spin.set_increments(1., 10.)
        spin.set_range(0., 100 * 365) # I presume 100 years is sufficient
        spin.connect("activate", self._activate_custom_span_cb)
        spin.connect("show", lambda w: w.grab_focus())

        label = gtk.Label("Days")

        entry.pack_start(spin, expand=False, fill=False)
        entry.pack_start(label, expand=False, fill=False)

        return entry


"""The "span-changed" signal is emitted when a new span has been selected or
entered.

Callback signature: def callback(SpanSelector, span, [user_param, ...])
"""
gobject.signal_new("span-changed", SpanSelector,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_FLOAT,))

"""The "custom-span-added" signal is emitted after a custom span has been
added, but before it has been selected.

Callback signature: def callback(SpanSelector, span, [user_param, ...])
"""
gobject.signal_new("custom-span-added", SpanSelector,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_FLOAT,))

