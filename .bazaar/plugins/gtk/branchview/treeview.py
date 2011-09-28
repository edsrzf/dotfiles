# -*- coding: UTF-8 -*-
"""Revision history view.

"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Daniel Schierbeck <daniel.schierbeck@gmail.com>"

import gtk
import gobject
import pango
import treemodel
from bzrlib import ui

from bzrlib.plugins.gtk.ui import ProgressPanel
from linegraph import linegraph, same_branch
from graphcell import CellRendererGraph
from treemodel import TreeModel
from bzrlib.revision import NULL_REVISION
from bzrlib.plugins.gtk import lock


class TreeView(gtk.VBox):

    __gproperties__ = {
        'branch': (gobject.TYPE_PYOBJECT,
                   'Branch',
                   'The Bazaar branch being visualized',
                   gobject.PARAM_CONSTRUCT_ONLY | gobject.PARAM_WRITABLE),

        'revision': (gobject.TYPE_PYOBJECT,
                     'Revision',
                     'The currently selected revision',
                     gobject.PARAM_READWRITE),

        'revision-number': (gobject.TYPE_STRING,
                            'Revision number',
                            'The number of the selected revision',
                            '',
                            gobject.PARAM_READABLE),

        'children': (gobject.TYPE_PYOBJECT,
                     'Child revisions',
                     'Children of the currently selected revision',
                     gobject.PARAM_READABLE),

        'parents': (gobject.TYPE_PYOBJECT,
                    'Parent revisions',
                    'Parents to the currently selected revision',
                    gobject.PARAM_READABLE),

        'revno-column-visible': (gobject.TYPE_BOOLEAN,
                                 'Revision number column',
                                 'Show revision number column',
                                 True,
                                 gobject.PARAM_READWRITE),

        'graph-column-visible': (gobject.TYPE_BOOLEAN,
                                 'Graph column',
                                 'Show graph column',
                                 True,
                                 gobject.PARAM_READWRITE),

        'date-column-visible': (gobject.TYPE_BOOLEAN,
                                 'Date',
                                 'Show date column',
                                 False,
                                 gobject.PARAM_READWRITE),

        'compact': (gobject.TYPE_BOOLEAN,
                    'Compact view',
                    'Break ancestry lines to save space',
                    True,
                    gobject.PARAM_CONSTRUCT | gobject.PARAM_READWRITE),

        'mainline-only': (gobject.TYPE_BOOLEAN,
                    'Mainline only',
                    'Only show the mainline history.',
                    False,
                    gobject.PARAM_CONSTRUCT | gobject.PARAM_READWRITE),

    }

    __gsignals__ = {
        'revision-selected': (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE,
                              ()),
        'revision-activated': (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE,
                              (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        'tag-added': (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE,
                              (gobject.TYPE_STRING, gobject.TYPE_STRING)),
        'refreshed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                              ())
    }

    def __init__(self, branch, start, maxnum, compact=True):
        """Create a new TreeView.

        :param branch: Branch object for branch to show.
        :param start: Revision id of top revision.
        :param maxnum: Maximum number of revisions to display, 
                       None for no limit.
        :param broken_line_length: After how much lines to break 
                                   branches.
        """
        gtk.VBox.__init__(self, spacing=0)

        self.progress_widget = ProgressPanel()
        self.pack_start(self.progress_widget, expand=False, fill=True)
        if getattr(ui.ui_factory, "set_progress_bar_widget", None) is not None:
            # We'are using our own ui, let's tell it to use our widget.
            ui.ui_factory.set_progress_bar_widget(self.progress_widget)

        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                        gtk.POLICY_AUTOMATIC)
        self.scrolled_window.set_shadow_type(gtk.SHADOW_IN)
        self.scrolled_window.show()
        self.pack_start(self.scrolled_window, expand=True, fill=True)

        self.scrolled_window.add(self.construct_treeview())

        self.path = None
        self.branch = branch
        self.revision = None
        self.index = {}

        self.start = start
        self.maxnum = maxnum
        self.compact = compact

        gobject.idle_add(self.populate)

        self.connect("destroy", self._on_destroy)

    def _on_destroy(self, *ignored):
        self.branch.unlock()
        if getattr(ui.ui_factory, "set_progress_bar_widget", None) is not None:
            # We'are using our own ui, let's tell it to stop using our widget.
            ui.ui_factory.set_progress_bar_widget(None)

    def do_get_property(self, property):
        if property.name == 'revno-column-visible':
            return self.revno_column.get_visible()
        elif property.name == 'graph-column-visible':
            return self.graph_column.get_visible()
        elif property.name == 'date-column-visible':
            return self.date_column.get_visible()
        elif property.name == 'compact':
            return self.compact
        elif property.name == 'mainline-only':
            return self.mainline_only
        elif property.name == 'branch':
            return self.branch
        elif property.name == 'revision':
            return self.model.get_value(self.model.get_iter(self.path),
                                        treemodel.REVISION)
        elif property.name == 'revision-number':
            return self.model.get_value(self.model.get_iter(self.path),
                                        treemodel.REVNO)
        elif property.name == 'children':
            return self.model.get_value(self.model.get_iter(self.path),
                                        treemodel.CHILDREN)
        elif property.name == 'parents':
            return self.model.get_value(self.model.get_iter(self.path),
                                        treemodel.PARENTS)
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def do_set_property(self, property, value):
        if property.name == 'revno-column-visible':
            self.revno_column.set_visible(value)
        elif property.name == 'graph-column-visible':
            self.graph_column.set_visible(value)
        elif property.name == 'date-column-visible':
            self.date_column.set_visible(value)
        elif property.name == 'compact':
            self.compact = value
        elif property.name == 'mainline-only':
            self.mainline_only = value
        elif property.name == 'branch':
            self.branch = value
        elif property.name == 'revision':
            self.set_revision_id(value.revision_id)
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def get_revision(self):
        """Return revision id of currently selected revision, or None."""
        return self.get_property('revision')

    def has_revision_id(self, revision_id):
        return (revision_id in self.index)

    def set_revision(self, revision):
        self.set_property('revision', revision)

    def set_revision_id(self, revid):
        """Change the currently selected revision.

        :param revid: Revision id of revision to display.
        """
        self.treeview.set_cursor(self.index[revid])
        self.treeview.grab_focus()

    def get_children(self):
        """Return the children of the currently selected revision.

        :return: list of revision ids.
        """
        return self.get_property('children')

    def get_parents(self):
        """Return the parents of the currently selected revision.

        :return: list of revision ids.
        """
        return self.get_property('parents')

    def add_tag(self, tag, revid=None):
        if revid is None: revid = self.revision.revision_id

        if lock.release(self.branch):
            try:
                lock.acquire(self.branch, lock.WRITE)
                self.model.add_tag(tag, revid)
            finally:
                lock.release(self.branch)

            lock.acquire(self.branch, lock.READ)

            self.emit('tag-added', tag, revid)
        
    def refresh(self):
        gobject.idle_add(self.populate, self.get_revision())

    def update(self):
        try:
            self.branch.unlock()
            try:
                self.branch.lock_write()
                self.branch.update()
            finally:
                self.branch.unlock()
        finally:
            self.branch.lock_read()

    def back(self):
        """Signal handler for the Back button."""
        parents = self.get_parents()
        if not len(parents):
            return

        for parent_id in parents:
            parent_index = self.index[parent_id]
            parent = self.model[parent_index][treemodel.REVISION]
            if same_branch(self.get_revision(), parent):
                self.set_revision(parent)
                break
        else:
            self.set_revision_id(parents[0])

    def forward(self):
        """Signal handler for the Forward button."""
        children = self.get_children()
        if not len(children):
            return

        for child_id in children:
            child_index = self.index[child_id]
            child = self.model[child_index][treemodel.REVISION]
            if same_branch(child, self.get_revision()):
                self.set_revision(child)
                break
        else:
            self.set_revision_id(children[0])

    def populate(self, revision=None):
        """Fill the treeview with contents.

        :param start: Revision id of revision to start with.
        :param maxnum: Maximum number of revisions to display, or None 
                       for no limit.
        :param broken_line_length: After how much lines branches \
                       should be broken.
        """

        if getattr(ui.ui_factory, "set_progress_bar_widget", None) is not None:
            # We'are using our own ui, let's tell it to use our widget.
            ui.ui_factory.set_progress_bar_widget(self.progress_widget)
        self.progress_bar = ui.ui_factory.nested_progress_bar()
        self.progress_bar.update("Loading ancestry graph", 0, 5)

        try:
            if self.compact:
                broken_line_length = 32
            else:
                broken_line_length = None
            
            show_graph = self.graph_column.get_visible()

            self.branch.lock_read()
            (linegraphdata, index, columns_len) = linegraph(self.branch.repository.get_graph(),
                                                            self.start,
                                                            self.maxnum, 
                                                            broken_line_length,
                                                            show_graph,
                                                            self.mainline_only,
                                                            self.progress_bar)

            self.model = TreeModel(self.branch, linegraphdata)
            self.graph_cell.columns_len = columns_len
            width = self.graph_cell.get_size(self.treeview)[2]
            if width > 500:
                width = 500
            self.graph_column.set_fixed_width(width)
            self.graph_column.set_max_width(width)
            self.index = index
            self.treeview.set_model(self.model)

            if not revision or revision == NULL_REVISION:
                self.treeview.set_cursor(0)
            else:
                self.set_revision(revision)

            self.emit('refreshed')
            return False
        finally:
            self.progress_bar.finished()

    def construct_treeview(self):
        self.treeview = gtk.TreeView()

        self.treeview.set_rules_hint(True)
        self.treeview.set_search_column(treemodel.REVNO)
        
        # Fix old PyGTK bug - by JAM
        set_tooltip = getattr(self.treeview, 'set_tooltip_column', None)
        if set_tooltip is not None:
            set_tooltip(treemodel.MESSAGE)

        self._prev_cursor_path = None
        self.treeview.connect("cursor-changed",
                self._on_selection_changed)

        self.treeview.connect("row-activated", 
                self._on_revision_activated)

        self.treeview.connect("button-release-event", 
                self._on_revision_selected)

        self.treeview.set_property('fixed-height-mode', True)

        self.treeview.show()

        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 15)
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        self.revno_column = gtk.TreeViewColumn("Revision No")
        self.revno_column.set_resizable(False)
        self.revno_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.revno_column.set_fixed_width(cell.get_size(self.treeview)[2])
        self.revno_column.pack_start(cell, expand=True)
        self.revno_column.add_attribute(cell, "text", treemodel.REVNO)
        self.treeview.append_column(self.revno_column)

        self.graph_cell = CellRendererGraph()
        self.graph_column = gtk.TreeViewColumn()
        self.graph_column.set_resizable(False)
        self.graph_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.graph_column.pack_start(self.graph_cell, expand=True)
        self.graph_column.add_attribute(self.graph_cell, "node", treemodel.NODE)
        self.graph_column.add_attribute(self.graph_cell, "tags", treemodel.TAGS)
        self.graph_column.add_attribute(self.graph_cell, "in-lines", treemodel.LAST_LINES)
        self.graph_column.add_attribute(self.graph_cell, "out-lines", treemodel.LINES)
        self.treeview.append_column(self.graph_column)

        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 65)
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        self.summary_column = gtk.TreeViewColumn("Summary")
        self.summary_column.set_resizable(False)
        self.summary_column.set_expand(True)
        self.summary_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.summary_column.set_fixed_width(cell.get_size(self.treeview)[2])
        self.summary_column.pack_start(cell, expand=True)
        self.summary_column.add_attribute(cell, "markup", treemodel.SUMMARY)
        self.treeview.append_column(self.summary_column)

        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 15)
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        self.authors_column = gtk.TreeViewColumn("Author(s)")
        self.authors_column.set_resizable(False)
        self.authors_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.authors_column.set_fixed_width(200)
        self.authors_column.pack_start(cell, expand=True)
        self.authors_column.add_attribute(cell, "text", treemodel.AUTHORS)
        self.treeview.append_column(self.authors_column)

        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 20)
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        self.date_column = gtk.TreeViewColumn("Date")
        self.date_column.set_visible(False)
        self.date_column.set_resizable(False)
        self.date_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.date_column.set_fixed_width(130)
        self.date_column.pack_start(cell, expand=True)
        self.date_column.add_attribute(cell, "text", treemodel.TIMESTAMP)
        self.treeview.append_column(self.date_column)
        
        return self.treeview
    
    def _on_selection_changed(self, treeview):
        """callback for when the treeview changes."""
        (path, focus) = treeview.get_cursor()
        if (path is not None) and (path != self._prev_cursor_path):
            self._prev_cursor_path = path # avoid emitting twice per click
            self.path = path
            self.emit('revision-selected')

    def _on_revision_selected(self, widget, event):
        from bzrlib.plugins.gtk.revisionmenu import RevisionMenu
        if event.button == 3:
            menu = RevisionMenu(self.branch.repository, 
                [self.get_revision().revision_id],
                self.branch)
            menu.connect('tag-added', lambda w, t, r: self.add_tag(t, r))
            menu.popup(None, None, None, event.button, event.get_time())

    def _on_revision_activated(self, widget, path, col):
        self.emit('revision-activated', path, col)
