# Copyright (C) 2007 by Jelmer Vernooij <jelmer@samba.org>
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

from bzrlib.branch import Branch
from bzrlib.config import GlobalConfig
import gtk
from history import UrlHistory
import gobject

class BranchSelectionBox(gtk.HBox):
    def __init__(self, path=None):
        gobject.GObject.__init__(self)
        self._combo = gtk.ComboBoxEntry()
        self._combo.child.connect('focus-out-event', self._on_combo_changed)
        
        # Build branch history
        self._history = UrlHistory(GlobalConfig(), 'branch_history')
        self._build_history()

        self.add(self._combo)

        if path is not None:
            self.set_url(path)

    def set_url(self, url):
        self._combo.get_child().set_text(url)

    def get_url(self):
        return self._combo.get_child().get_text()

    def get_branch(self):
        return Branch.open(self.get_url())

    def _build_history(self):
        """ Build up the branch history. """
        self._combo_model = gtk.ListStore(str)
        
        for item in self._history.get_entries():
            self._combo_model.append([ item ])
        
        self._combo.set_model(self._combo_model)
        self._combo.set_text_column(0)

    def _on_combo_changed(self, widget, event):
        self.emit('branch-changed', widget)

gobject.signal_new('branch-changed', BranchSelectionBox, 
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE, (gobject.TYPE_OBJECT,))
gobject.type_register(BranchSelectionBox)
