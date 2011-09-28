# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
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

import time

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import gobject
import gtk

from bzrlib.osutils import format_date
from bzrlib.plugins.gtk import _i18n
from bzrlib.plugins.gtk.branchview.treeview import TreeView


class RevisionBrowser(gtk.Dialog):
    """ Revision Browser main window. """
    def __init__(self, branch, parent=None):
        gtk.Dialog.__init__(self, title="Revision Browser - Olive",
                                  parent=parent,
                                  flags=gtk.DIALOG_MODAL,
                                  buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
    
        # Get arguments
        self.branch = branch
        
        # Create the widgets
        self._button_select = gtk.Button(_i18n("_Select"), use_underline=True)
        start_revs = [branch.last_revision(),]
        self.treeview = TreeView(branch, start_revs, None)
        
        # Set callbacks
        self._button_select.connect('clicked', self._on_select_clicked)
        self.treeview.connect('revision-activated',
                               self._on_treeview_revision_activated)
        
        # Set properties
        self.set_default_size(600, 400)
        self.vbox.set_spacing(3)
        self.treeview.set_property('graph-column-visible', False)
        self.treeview.set_property('date-column-visible', True)
        self.treeview.set_property('mainline-only', True)
        
        # Construct the dialog
        self.action_area.pack_end(self._button_select)
        
        self.vbox.pack_start(self.treeview, True, True)

        # Show the dialog
        self.show_all()

    
    def _on_treeview_revision_activated(self, treeview, path, column):
        """ Double-click on a row should also select a revision. """
        self._on_select_clicked(treeview)
    
    def _on_select_clicked(self, widget):
        """ Select button clicked handler. """
        
        self.selected_revno = self.treeview.get_property('revision-number')
        self.selected_revid = \
                    self.treeview.get_property('revision').revision_id
        self.response(gtk.RESPONSE_OK)
