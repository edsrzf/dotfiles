"""Branch window.

This module contains the code to manage the branch information window,
which contains both the revision graph and details panes.
"""

__copyright__ = "Copyright (c) 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"


import gtk

from bzrlib.plugins.gtk import icon_path
from bzrlib.plugins.gtk.branchview import TreeView
from bzrlib.plugins.gtk.preferences import PreferencesWindow
from bzrlib.plugins.gtk.revisionmenu import RevisionMenu
from bzrlib.plugins.gtk.window import Window

from bzrlib.config import GlobalConfig
from bzrlib.revision import NULL_REVISION
from bzrlib.trace import mutter

class BranchWindow(Window):
    """Branch window.

    This object represents and manages a single window containing information
    for a particular branch.
    """

    def __init__(self, branch, start_revs, maxnum, parent=None):
        """Create a new BranchWindow.

        :param branch: Branch object for branch to show.
        :param start_revs: Revision ids of top revisions.
        :param maxnum: Maximum number of revisions to display, 
                       None for no limit.
        """

        Window.__init__(self, parent=parent)
        self.set_border_width(0)

        self.branch      = branch
        self.start_revs  = start_revs
        self.maxnum      = maxnum
        self.config      = GlobalConfig()

        if self.config.get_user_option('viz-compact-view') == 'yes':
            self.compact_view = True
        else:
            self.compact_view = False

        self.set_title(branch._get_nick(local=True) + " - revision history")

        # user-configured window size
        size = self._load_size('viz-window-size')
        if size:
            width, height = size
        else:
            # Use three-quarters of the screen by default
            screen = self.get_screen()
            monitor = screen.get_monitor_geometry(0)
            width = int(monitor.width * 0.75)
            height = int(monitor.height * 0.75)
        self.set_default_size(width, height)
        self.set_size_request(width/3, height/3)
        self._save_size_on_destroy(self, 'viz-window-size')

        # FIXME AndyFitz!
        icon = self.render_icon(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON)
        self.set_icon(icon)

        gtk.accel_map_add_entry("<viz>/Go/Next Revision", gtk.keysyms.Up, gtk.gdk.MOD1_MASK)
        gtk.accel_map_add_entry("<viz>/Go/Previous Revision", gtk.keysyms.Down, gtk.gdk.MOD1_MASK)
        gtk.accel_map_add_entry("<viz>/View/Refresh", gtk.keysyms.F5, 0)

        self.accel_group = gtk.AccelGroup()
        self.add_accel_group(self.accel_group)

        if getattr(gtk.Action, 'set_tool_item_type', None) is not None:
            # Not available before PyGtk-2.10
            gtk.Action.set_tool_item_type(gtk.MenuToolButton)

        self.prev_rev_action = gtk.Action("prev-rev", "_Previous Revision", "Go to the previous revision", gtk.STOCK_GO_DOWN)
        self.prev_rev_action.set_accel_path("<viz>/Go/Previous Revision")
        self.prev_rev_action.set_accel_group(self.accel_group)
        self.prev_rev_action.connect("activate", self._back_clicked_cb)
        self.prev_rev_action.connect_accelerator()

        self.next_rev_action = gtk.Action("next-rev", "_Next Revision", "Go to the next revision", gtk.STOCK_GO_UP)
        self.next_rev_action.set_accel_path("<viz>/Go/Next Revision")
        self.next_rev_action.set_accel_group(self.accel_group)
        self.next_rev_action.connect("activate", self._fwd_clicked_cb)
        self.next_rev_action.connect_accelerator()

        self.refresh_action = gtk.Action("refresh", "_Refresh", "Refresh view", gtk.STOCK_REFRESH)
        self.refresh_action.set_accel_path("<viz>/View/Refresh")
        self.refresh_action.set_accel_group(self.accel_group)
        self.refresh_action.connect("activate", self._refresh_clicked)
        self.refresh_action.connect_accelerator()

        self.construct()

    def _save_size_on_destroy(self, widget, config_name):
        """Creates a hook that saves the size of widget to config option 
           config_name when the window is destroyed/closed."""
        def save_size(src):
            width, height = widget.allocation.width, widget.allocation.height
            value = '%sx%s' % (width, height)
            self.config.set_user_option(config_name, value)
        self.connect("destroy", save_size)

    def set_revision(self, revid):
        self.treeview.set_revision_id(revid)

    def construct(self):
        """Construct the window contents."""
        vbox = gtk.VBox(spacing=0)
        self.add(vbox)

        self.paned = gtk.VPaned()
        self.paned.pack1(self.construct_top(), resize=False, shrink=True)
        self.paned.pack2(self.construct_bottom(), resize=True, shrink=False)
        self.paned.show()

        nav = self.construct_navigation()
        menubar = self.construct_menubar()
        vbox.pack_start(menubar, expand=False, fill=True)
        vbox.pack_start(nav, expand=False, fill=True)

        vbox.pack_start(self.paned, expand=True, fill=True)
        vbox.set_focus_child(self.paned)

        self.treeview.connect('revision-selected',
                self._treeselection_changed_cb)
        self.treeview.connect('revision-activated',
                self._tree_revision_activated)

        self.treeview.connect('tag-added', lambda w, t, r: self._update_tags())
        vbox.show()

    def construct_menubar(self):
        menubar = gtk.MenuBar()

        file_menu = gtk.Menu()
        file_menuitem = gtk.MenuItem("_File")
        file_menuitem.set_submenu(file_menu)

        file_menu_close = gtk.ImageMenuItem(gtk.STOCK_CLOSE, self.accel_group)
        file_menu_close.connect('activate', lambda x: self.destroy())

        file_menu_quit = gtk.ImageMenuItem(gtk.STOCK_QUIT, self.accel_group)
        file_menu_quit.connect('activate', lambda x: gtk.main_quit())

        if self._parent is not None:
            file_menu.add(file_menu_close)
        file_menu.add(file_menu_quit)

        edit_menu = gtk.Menu()
        edit_menuitem = gtk.MenuItem("_Edit")
        edit_menuitem.set_submenu(edit_menu)

        edit_menu_branchopts = gtk.MenuItem("Branch Settings")
        edit_menu_branchopts.connect('activate', lambda x: PreferencesWindow(self.branch.get_config()).show())

        edit_menu_globopts = gtk.MenuItem("Global Settings")
        edit_menu_globopts.connect('activate', lambda x: PreferencesWindow().show())

        edit_menu.add(edit_menu_branchopts)
        edit_menu.add(edit_menu_globopts)

        view_menu = gtk.Menu()
        view_menuitem = gtk.MenuItem("_View")
        view_menuitem.set_submenu(view_menu)

        view_menu_refresh = self.refresh_action.create_menu_item()
        view_menu_refresh.connect('activate', self._refresh_clicked)

        view_menu.add(view_menu_refresh)
        view_menu.add(gtk.SeparatorMenuItem())

        view_menu_toolbar = gtk.CheckMenuItem("Show Toolbar")
        view_menu_toolbar.set_active(True)
        if self.config.get_user_option('viz-toolbar-visible') == 'False':
            view_menu_toolbar.set_active(False)
            self.toolbar.hide()
        view_menu_toolbar.connect('toggled', self._toolbar_visibility_changed)

        view_menu_compact = gtk.CheckMenuItem("Show Compact Graph")
        view_menu_compact.set_active(self.compact_view)
        view_menu_compact.connect('activate', self._brokenlines_toggled_cb)

        view_menu_diffs = gtk.CheckMenuItem("Show Diffs")
        view_menu_diffs.set_active(False)
        if self.config.get_user_option('viz-show-diffs') == 'True':
            view_menu_diffs.set_active(True)
        view_menu_diffs.connect('toggled', self._diff_visibility_changed)

        view_menu_wide_diffs = gtk.CheckMenuItem("Wide Diffs")
        view_menu_wide_diffs.set_active(False)
        if self.config.get_user_option('viz-wide-diffs') == 'True':
            view_menu_wide_diffs.set_active(True)
        view_menu_wide_diffs.connect('toggled', self._diff_placement_changed)

        view_menu_wrap_diffs = gtk.CheckMenuItem("Wrap _Long Lines in Diffs")
        view_menu_wrap_diffs.set_active(False)
        if self.config.get_user_option('viz-wrap-diffs') == 'True':
            view_menu_wrap_diffs.set_active(True)
        view_menu_wrap_diffs.connect('toggled', self._diff_wrap_changed)

        view_menu.add(view_menu_toolbar)
        view_menu.add(view_menu_compact)
        view_menu.add(gtk.SeparatorMenuItem())
        view_menu.add(view_menu_diffs)
        view_menu.add(view_menu_wide_diffs)
        view_menu.add(view_menu_wrap_diffs)
        view_menu.add(gtk.SeparatorMenuItem())

        self.mnu_show_revno_column = gtk.CheckMenuItem("Show Revision _Number Column")
        self.mnu_show_date_column = gtk.CheckMenuItem("Show _Date Column")

        # Revision numbers are pointless if there are multiple branches
        if len(self.start_revs) > 1:
            self.mnu_show_revno_column.set_sensitive(False)
            self.treeview.set_property('revno-column-visible', False)

        for (col, name) in [(self.mnu_show_revno_column, "revno"), 
                            (self.mnu_show_date_column, "date")]:
            col.set_active(self.treeview.get_property(name + "-column-visible"))
            col.connect('toggled', self._col_visibility_changed, name)
            view_menu.add(col)

        go_menu = gtk.Menu()
        go_menu.set_accel_group(self.accel_group)
        go_menuitem = gtk.MenuItem("_Go")
        go_menuitem.set_submenu(go_menu)

        go_menu_next = self.next_rev_action.create_menu_item()
        go_menu_prev = self.prev_rev_action.create_menu_item()

        tag_image = gtk.Image()
        tag_image.set_from_file(icon_path("tag-16.png"))
        self.go_menu_tags = gtk.ImageMenuItem("_Tags")
        self.go_menu_tags.set_image(tag_image)
        self.treeview.connect('refreshed', lambda w: self._update_tags())

        go_menu.add(go_menu_next)
        go_menu.add(go_menu_prev)
        go_menu.add(gtk.SeparatorMenuItem())
        go_menu.add(self.go_menu_tags)

        self.revision_menu = RevisionMenu(self.branch.repository, [], self.branch, parent=self)
        revision_menuitem = gtk.MenuItem("_Revision")
        revision_menuitem.set_submenu(self.revision_menu)

        branch_menu = gtk.Menu()
        branch_menuitem = gtk.MenuItem("_Branch")
        branch_menuitem.set_submenu(branch_menu)

        branch_menu.add(gtk.MenuItem("Pu_ll Revisions"))
        branch_menu.add(gtk.MenuItem("Pu_sh Revisions"))

        try:
            from bzrlib.plugins import search
        except ImportError:
            mutter("Didn't find search plugin")
        else:
            branch_menu.add(gtk.SeparatorMenuItem())

            branch_index_menuitem = gtk.MenuItem("_Index")
            branch_index_menuitem.connect('activate', self._branch_index_cb)
            branch_menu.add(branch_index_menuitem)

            branch_search_menuitem = gtk.MenuItem("_Search")
            branch_search_menuitem.connect('activate', self._branch_search_cb)
            branch_menu.add(branch_search_menuitem)

        help_menu = gtk.Menu()
        help_menuitem = gtk.MenuItem("_Help")
        help_menuitem.set_submenu(help_menu)

        help_about_menuitem = gtk.ImageMenuItem(gtk.STOCK_ABOUT, self.accel_group)
        help_about_menuitem.connect('activate', self._about_dialog_cb)

        help_menu.add(help_about_menuitem)

        menubar.add(file_menuitem)
        menubar.add(edit_menuitem)
        menubar.add(view_menuitem)
        menubar.add(go_menuitem)
        menubar.add(revision_menuitem)
        menubar.add(branch_menuitem)
        menubar.add(help_menuitem)
        menubar.show_all()

        return menubar

    def construct_top(self):
        """Construct the top-half of the window."""
        # FIXME: Make broken_line_length configurable

        self.treeview = TreeView(self.branch, self.start_revs, self.maxnum, self.compact_view)

        for col in ["revno", "date"]:
            option = self.config.get_user_option(col + '-column-visible')
            if option is not None:
                self.treeview.set_property(col + '-column-visible', option == 'True')
            else:
                self.treeview.set_property(col + '-column-visible', False)

        self.treeview.show()

        align = gtk.Alignment(0.0, 0.0, 1.0, 1.0)
        align.set_padding(5, 0, 0, 0)
        align.add(self.treeview)
        # user-configured size
        size = self._load_size('viz-graph-size')
        if size:
            width, height = size
            align.set_size_request(width, height)
        else:
            (width, height) = self.get_size()
            align.set_size_request(width, int(height / 2.5))
        self._save_size_on_destroy(align, 'viz-graph-size')
        align.show()

        return align

    def construct_navigation(self):
        """Construct the navigation buttons."""
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_BOTH_HORIZ)

        self.prev_button = self.prev_rev_action.create_tool_item()
        self.toolbar.insert(self.prev_button, -1)

        self.next_button = self.next_rev_action.create_tool_item()
        self.toolbar.insert(self.next_button, -1)

        self.toolbar.insert(gtk.SeparatorToolItem(), -1)

        refresh_button = gtk.ToolButton(gtk.STOCK_REFRESH)
        refresh_button.connect('clicked', self._refresh_clicked)
        self.toolbar.insert(refresh_button, -1)

        self.toolbar.show_all()

        return self.toolbar

    def construct_bottom(self):
        """Construct the bottom half of the window."""
        if self.config.get_user_option('viz-wide-diffs') == 'True':
            self.diff_paned = gtk.VPaned()
        else:
            self.diff_paned = gtk.HPaned()
        (width, height) = self.get_size()
        self.diff_paned.set_size_request(20, 20) # shrinkable

        from bzrlib.plugins.gtk.revisionview import RevisionView
        self.revisionview = RevisionView(branch=self.branch)
        self.revisionview.set_size_request(width/3, int(height / 2.5))
        # user-configured size
        size = self._load_size('viz-revisionview-size')
        if size:
            width, height = size
            self.revisionview.set_size_request(width, height)
        self._save_size_on_destroy(self.revisionview, 'viz-revisionview-size')
        self.revisionview.show()
        self.revisionview.set_show_callback(self._show_clicked_cb)
        self.revisionview.connect('notify::revision', self._go_clicked_cb)
        self.treeview.connect('tag-added', lambda w, t, r: self.revisionview.update_tags())
        self.diff_paned.pack1(self.revisionview)

        from bzrlib.plugins.gtk.diff import DiffWidget
        self.diff = DiffWidget()
        self.diff_paned.pack2(self.diff)

        self.diff_paned.show_all()
        if self.config.get_user_option('viz-show-diffs') != 'True':
            self.diff.hide()

        return self.diff_paned

    def _tag_selected_cb(self, menuitem, revid):
        self.treeview.set_revision_id(revid)

    def _treeselection_changed_cb(self, selection, *args):
        """callback for when the treeview changes."""
        revision = self.treeview.get_revision()
        parents  = self.treeview.get_parents()
        children = self.treeview.get_children()

        self.revision_menu.set_revision_ids([revision.revision_id])

        if revision and revision != NULL_REVISION:
            prev_menu = gtk.Menu()
            if len(parents) > 0:
                self.prev_rev_action.set_sensitive(True)
                for parent_id in parents:
                    if parent_id and parent_id != NULL_REVISION:
                        parent = self.branch.repository.get_revision(parent_id)
                        try:
                            str = ' (' + parent.properties['branch-nick'] + ')'
                        except KeyError:
                            str = ""

                        item = gtk.MenuItem(parent.message.split("\n")[0] + str)
                        item.connect('activate', self._set_revision_cb, parent_id)
                        prev_menu.add(item)
                prev_menu.show_all()
            else:
                self.prev_rev_action.set_sensitive(False)
                prev_menu.hide()

            if getattr(self.prev_button, 'set_menu', None) is not None:
		self.prev_button.set_menu(prev_menu)

            next_menu = gtk.Menu()
            if len(children) > 0:
                self.next_rev_action.set_sensitive(True)
                for child_id in children:
                    child = self.branch.repository.get_revision(child_id)
                    try:
                        str = ' (' + child.properties['branch-nick'] + ')'
                    except KeyError:
                        str = ""

                    item = gtk.MenuItem(child.message.split("\n")[0] + str)
                    item.connect('activate', self._set_revision_cb, child_id)
                    next_menu.add(item)
                next_menu.show_all()
            else:
                self.next_rev_action.set_sensitive(False)
                next_menu.hide()

            if getattr(self.next_button, 'set_menu', None) is not None:
		self.next_button.set_menu(next_menu)

            self.revisionview.set_revision(revision)
            self.revisionview.set_children(children)
            self.update_diff_panel(revision, parents)

    def _tree_revision_activated(self, widget, path, col):
        # TODO: more than one parent
        """Callback for when a treeview row gets activated."""
        revision = self.treeview.get_revision()
        parents  = self.treeview.get_parents()

        if len(parents) == 0:
            parent_id = NULL_REVISION
        else:
            parent_id = parents[0]

        self.show_diff(revision.revision_id, parent_id)
        self.treeview.grab_focus()

    def _back_clicked_cb(self, *args):
        """Callback for when the back button is clicked."""
        self.treeview.back()

    def _fwd_clicked_cb(self, *args):
        """Callback for when the forward button is clicked."""
        self.treeview.forward()

    def _go_clicked_cb(self, w, p):
        """Callback for when the go button for a parent is clicked."""
        if self.revisionview.get_revision() is not None:
            self.treeview.set_revision(self.revisionview.get_revision())

    def _show_clicked_cb(self, revid, parentid):
        """Callback for when the show button for a parent is clicked."""
        self.show_diff(revid, parentid)
        self.treeview.grab_focus()

    def _set_revision_cb(self, w, revision_id):
        self.treeview.set_revision_id(revision_id)

    def _brokenlines_toggled_cb(self, button):
        self.compact_view = button.get_active()

        if self.compact_view:
            option = 'yes'
        else:
            option = 'no'

        self.config.set_user_option('viz-compact-view', option)
        self.treeview.set_property('compact', self.compact_view)
        self.treeview.refresh()

    def _branch_index_cb(self, w):
        from bzrlib.plugins.search import index as _mod_index
        _mod_index.index_url(self.branch.base)

    def _branch_search_cb(self, w):
        from bzrlib.plugins.search import index as _mod_index
        from bzrlib.plugins.gtk.search import SearchDialog
        from bzrlib.plugins.search import errors as search_errors

        try:
            index = _mod_index.open_index_url(self.branch.base)
        except search_errors.NoSearchIndex:
            dialog = gtk.MessageDialog(self, type=gtk.MESSAGE_QUESTION, 
                buttons=gtk.BUTTONS_OK_CANCEL, 
                message_format="This branch has not been indexed yet. "
                               "Index now?")
            if dialog.run() == gtk.RESPONSE_OK:
                dialog.destroy()
                index = _mod_index.index_url(self.branch.base)
            else:
                dialog.destroy()
                return

        dialog = SearchDialog(index)

        if dialog.run() == gtk.RESPONSE_OK:
            self.set_revision(dialog.get_revision())

        dialog.destroy()

    def _about_dialog_cb(self, w):
        from bzrlib.plugins.gtk.about import AboutDialog
        AboutDialog().run()

    def _col_visibility_changed(self, col, property):
        self.config.set_user_option(property + '-column-visible', col.get_active())
        self.treeview.set_property(property + '-column-visible', col.get_active())

    def _toolbar_visibility_changed(self, col):
        if col.get_active():
            self.toolbar.show()
        else:
            self.toolbar.hide()
        self.config.set_user_option('viz-toolbar-visible', col.get_active())

    def _make_diff_nonzero_size(self):
        """make sure the diff isn't zero-width or zero-height"""
        alloc = self.diff.get_allocation()
        if (alloc.width < 10) or (alloc.height < 10):
            width, height = self.get_size()
            self.revisionview.set_size_request(width/3, int(height / 2.5))

    def _diff_visibility_changed(self, col):
        """Hide or show the diff panel."""
        if col.get_active():
            self.diff.show()
            self._make_diff_nonzero_size()
        else:
            self.diff.hide()
        self.config.set_user_option('viz-show-diffs', str(col.get_active()))
        self.update_diff_panel()

    def _diff_placement_changed(self, col):
        """Toggle the diff panel's position."""
        self.config.set_user_option('viz-wide-diffs', str(col.get_active()))

        old = self.paned.get_child2()
        self.paned.remove(old)
        self.paned.pack2(self.construct_bottom(), resize=True, shrink=False)
        self._make_diff_nonzero_size()

        self.treeview.emit('revision-selected')

    def _diff_wrap_changed(self, widget):
        """Toggle word wrap in the diff widget."""
        self.config.set_user_option('viz-wrap-diffs', widget.get_active())
        self.diff._on_wraplines_toggled(widget)

    def _refresh_clicked(self, w):
        self.treeview.refresh()

    def _update_tags(self):
        menu = gtk.Menu()

        if self.branch.supports_tags():
            tags = self.branch.tags.get_tag_dict().items()
            tags.sort(reverse=True)
            for tag, revid in tags:
                tag_image = gtk.Image()
                tag_image.set_from_file(icon_path('tag-16.png'))
                tag_item = gtk.ImageMenuItem(tag.replace('_', '__'))
                tag_item.set_image(tag_image)
                tag_item.connect('activate', self._tag_selected_cb, revid)
                tag_item.set_sensitive(self.treeview.has_revision_id(revid))
                menu.add(tag_item)
            self.go_menu_tags.set_submenu(menu)

            self.go_menu_tags.set_sensitive(len(tags) != 0)
        else:
            self.go_menu_tags.set_sensitive(False)

        self.go_menu_tags.show_all()

    def _load_size(self, name):
        """Read and parse 'name' from self.config.
        The value is a string, formatted as WIDTHxHEIGHT
        Returns None, or (width, height)
        """
        size = self.config.get_user_option(name)
        if size:
            width, height = [int(num) for num in size.split('x')]
            # avoid writing config every time we start
            return width, height
        return None

    def show_diff(self, revid=None, parentid=NULL_REVISION):
        """Open a new window to show a diff between the given revisions."""
        from bzrlib.plugins.gtk.diff import DiffWindow
        window = DiffWindow(parent=self)

        rev_tree    = self.branch.repository.revision_tree(revid)
        parent_tree = self.branch.repository.revision_tree(parentid)

        description = revid + " - " + self.branch._get_nick(local=True)
        window.set_diff(description, rev_tree, parent_tree)
        window.show()

    def update_diff_panel(self, revision=None, parents=None):
        """Show the current revision in the diff panel."""
        if self.config.get_user_option('viz-show-diffs') != 'True':
            return

        if not revision: # default to selected row
            revision = self.treeview.get_revision()
        if revision == NULL_REVISION:
            return

        if not parents: # default to selected row's parents
            parents  = self.treeview.get_parents()
        if len(parents) == 0:
            parent_id = NULL_REVISION
        else:
            parent_id = parents[0]

        rev_tree    = self.branch.repository.revision_tree(revision.revision_id)
        parent_tree = self.branch.repository.revision_tree(parent_id)

        self.diff.set_diff(rev_tree, parent_tree)
        if self.config.get_user_option('viz-wrap-diffs') == 'True':
            self.diff._on_wraplines_toggled(wrap=True)
        self.diff.show_all()
