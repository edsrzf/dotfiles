# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
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
    
import gtk

from errors import show_bzr_error

from bzrlib.config import LocationConfig
import bzrlib.errors as errors

from bzrlib.plugins.gtk import _i18n
from dialog import error_dialog, info_dialog, question_dialog

from history import UrlHistory

class PushDialog(gtk.Dialog):
    """ New implementation of the Push dialog. """
    def __init__(self, repository, revid, branch=None, parent=None):
        """ Initialize the Push dialog. """
        gtk.Dialog.__init__(self, title="Push - Olive",
                                  parent=parent,
                                  flags=0,
                                  buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        
        # Get arguments
        self.repository = repository
        self.revid = revid
        self.branch = branch
        
        # Create the widgets
        self._label_location = gtk.Label(_i18n("Location:"))
        self._combo = gtk.ComboBoxEntry()
        self._button_push = gtk.Button(_i18n("_Push"), use_underline=True)
        self._hbox_location = gtk.HBox()
        
        # Set callbacks
        self._button_push.connect('clicked', self._on_push_clicked)
        
        # Set properties
        self._label_location.set_alignment(0, 0.5)
        self._hbox_location.set_spacing(3)
        self.vbox.set_spacing(3)
        
        # Pack widgets
        self._hbox_location.pack_start(self._label_location, False, False)
        self._hbox_location.pack_start(self._combo, True, True)
        self.vbox.pack_start(self._hbox_location)
        self.action_area.pack_end(self._button_push)
        
        # Show the dialog
        self.vbox.show_all()
        
        # Build location history
        self._history = UrlHistory(self.branch.get_config(), 'push_history')
        self._build_history()
        
    def _build_history(self):
        """ Build up the location history. """
        self._combo_model = gtk.ListStore(str)
        for item in self._history.get_entries():
            self._combo_model.append([ item ])
        self._combo.set_model(self._combo_model)
        self._combo.set_text_column(0)
        
        if self.branch is not None:
            location = self.branch.get_push_location()
            if location is not None:
                self._combo.get_child().set_text(location)
    
    @show_bzr_error
    def _on_push_clicked(self, widget):
        """ Push button clicked handler. """
        location = self._combo.get_child().get_text()
        revs = 0
        
        try:
            revs = do_push(self.branch, location=location, overwrite=False)
        except errors.DivergedBranches:
            response = question_dialog(_i18n('Branches have been diverged'),
                                       _i18n('You cannot push if branches have diverged.\nOverwrite?'))
            if response == gtk.RESPONSE_YES:
                revs = do_push(self.branch, location=location, overwrite=True)
        
        if self.branch is not None and self.branch.get_push_location() is None:
            self.branch.set_push_location(location)
        
        self._history.add_entry(location)
        info_dialog(_i18n('Push successful'),
                    _i18n("%d revision(s) pushed.") % revs)
        
        self.response(gtk.RESPONSE_OK)

def do_push(br_from, location, overwrite):
    """ Update a mirror of a branch.
    
    :param br_from: the source branch
    
    :param location: the location of the branch that you'd like to update
    
    :param overwrite: overwrite target location if it diverged
    
    :return: number of revisions pushed
    """
    from bzrlib.bzrdir import BzrDir
    from bzrlib.transport import get_transport
        
    transport = get_transport(location)
    location_url = transport.base

    old_rh = []

    try:
        dir_to = BzrDir.open(location_url)
        br_to = dir_to.open_branch()
    except errors.NotBranchError:
        # create a branch.
        transport = transport.clone('..')
        try:
            relurl = transport.relpath(location_url)
            transport.mkdir(relurl)
        except errors.NoSuchFile:
            response = question_dialog(_i18n('Non existing parent directory'),
                         _i18n("The parent directory (%s)\ndoesn't exist. Create?") % location)
            if response == gtk.RESPONSE_OK:
                transport.create_prefix()
            else:
                return
        dir_to = br_from.bzrdir.clone(location_url,
            revision_id=br_from.last_revision())
        br_to = dir_to.open_branch()
        count = len(br_to.revision_history())
    else:
        old_rh = br_to.revision_history()
        try:
            tree_to = dir_to.open_workingtree()
        except errors.NotLocalUrl:
            # FIXME - what to do here? how should we warn the user?
            count = br_to.pull(br_from, overwrite)
        except errors.NoWorkingTree:
            count = br_to.pull(br_from, overwrite)
        else:
            count = tree_to.pull(br_from, overwrite)

    return count
