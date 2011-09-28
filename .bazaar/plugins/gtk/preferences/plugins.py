# Copyright (C) 2008 Jelmer Vernooij <jelmer@samba.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import gtk

class PluginsPage(gtk.VPaned):

    def __init__(self):
        gtk.VPaned.__init__(self)
        self.set_border_width(12)
        self.set_position(216)

        scrolledwindow = gtk.ScrolledWindow()
        scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolledwindow.set_shadow_type(gtk.SHADOW_IN)
        self.model = gtk.ListStore(str, str)
        treeview = gtk.TreeView()
        scrolledwindow.add(treeview)
        self.pack1(scrolledwindow, resize=True, shrink=False)

        self.table = gtk.Table(columns=2)
        self.table.set_border_width(12)
        self.table.set_row_spacings(6)
        self.table.set_col_spacings(6)

        treeview.set_headers_visible(False)
        treeview.set_model(self.model)
        treeview.connect("row-activated", self.row_selected)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn()
        column.pack_start(cell, expand=True)
        column.add_attribute(cell, "text", 0)
        treeview.append_column(column)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn()
        column.pack_start(cell, expand=True)
        column.add_attribute(cell, "text", 1)
        treeview.append_column(column)

        import bzrlib.plugin
        plugins = bzrlib.plugin.plugins()
        plugin_names = plugins.keys()
        plugin_names.sort()
        for name in plugin_names:
            self.model.append([name, getattr(plugins[name], '__file__', None)])

        scrolledwindow = gtk.ScrolledWindow()
        scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolledwindow.add_with_viewport(self.table)
        self.pack2(scrolledwindow, resize=False, shrink=True)
        self.show()

    def row_selected(self, tv, path, tvc):
        import bzrlib
        p = bzrlib.plugin.plugins()[self.model[path][0]].module
        from inspect import getdoc

        for w in self.table.get_children():
            self.table.remove(w)

        if getattr(p, '__author__', None) is not None:
            align = gtk.Alignment(0.0, 0.5)
            label = gtk.Label()
            label.set_markup("<b>Author:</b>")
            align.add(label)
            self.table.attach(align, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
            align.show()
            label.show()

            align = gtk.Alignment(0.0, 0.5)
            author = gtk.Label()
            author.set_text(p.__author__)
            author.set_selectable(True)
            align.add(author)
            self.table.attach(align, 1, 2, 0, 1, gtk.EXPAND | gtk.FILL, gtk.FILL)

        if getattr(p, '__version__', None) is not None:
            align = gtk.Alignment(0.0, 0.5)
            label = gtk.Label()
            label.set_markup("<b>Version:</b>")
            align.add(label)
            self.table.attach(align, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
            align.show()
            label.show()

            align = gtk.Alignment(0.0, 0.5)
            author = gtk.Label()
            author.set_text(p.__version__)
            author.set_selectable(True)
            align.add(author)
            self.table.attach(align, 1, 2, 0, 1, gtk.EXPAND | gtk.FILL, gtk.FILL)

        if getdoc(p) is not None:
            align = gtk.Alignment(0.0, 0.5)
            description = gtk.Label()
            description.set_text(getdoc(p))
            description.set_selectable(True)
            align.add(description)
            self.table.attach(align, 0, 2, 1, 2, gtk.EXPAND | gtk.FILL, gtk.FILL)

        self.table.show_all()


