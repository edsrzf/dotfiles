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
"""Simple popup menu for revisions."""

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import bzrlib
import gtk
import gobject
from bzrlib import (errors, ui)
from bzrlib.revision import NULL_REVISION

class RevisionMenu(gtk.Menu):

    __gsignals__ = {
            'tag-added': (
                gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (gobject.TYPE_STRING, gobject.TYPE_STRING)
            )
    }

    def __init__(self, repository, revids, branch=None, wt=None, parent=None):
        super(RevisionMenu, self).__init__()
        self._parent = parent
        self.branch = branch
        self.repository = repository
        self.wt = wt
        self.set_revision_ids(revids)

    def set_revision_ids(self, revids):
        assert isinstance(revids, list)
        for c in self.get_children():
            self.remove(c)
        self.revids = revids
        self.create_items()

    def create_items(self):
        if len(self.revids) == 1:
            item = gtk.MenuItem("View _Changes")
            item.connect('activate', self.show_diff)
            self.append(item)

            item = gtk.MenuItem("_Push")
            item.connect('activate', self.show_push)
            self.append(item)

            item = gtk.MenuItem("_Tag Revision")
            item.connect('activate', self.show_tag)
            self.append(item)

            item = gtk.MenuItem("_Merge Directive")
            item.connect('activate', self.store_merge_directive)
            # FIXME: self.append(item)

            item = gtk.MenuItem("_Send Merge Directive")
            item.connect('activate', self.send_merge_directive)
            self.append(item)
            
            if self.wt:
                item = gtk.MenuItem("_Revert to this revision")
                item.connect('activate', self.revert)
                self.append(item)

        self.show_all()

    def store_merge_directive(self, item):
        from bzrlib.plugins.gtk.mergedirective import CreateMergeDirectiveDialog
        window = CreateMergeDirectiveDialog(self.branch, self.revids[0])
        window.show()

    def send_merge_directive(self, item):
        from bzrlib.plugins.gtk.mergedirective import SendMergeDirectiveDialog
        from cStringIO import StringIO
        window = SendMergeDirectiveDialog(self.branch, self.revids[0])
        if window.run() == gtk.RESPONSE_OK:
            outf = StringIO()
            outf.writelines(window.get_merge_directive().to_lines())
            mail_client = self.branch.get_config().get_mail_client()
            mail_client.compose_merge_request(window.get_mail_to(), "[MERGE]",
                                              outf.getvalue())
        window.destroy()

    def show_diff(self, item):
        from bzrlib.plugins.gtk.diff import DiffWindow
        window = DiffWindow(parent=self._parent)
        parentids = self.repository.get_revision(self.revids[0]).parent_ids
        if len(parentids) == 0:
            parentid = NULL_REVISION
        else:
            parentid = parentids[0]
        rev_tree    = self.repository.revision_tree(self.revids[0])
        parent_tree = self.repository.revision_tree(parentid)
        window.set_diff(self.revids[0], rev_tree, parent_tree)
        window.show()

    def show_push(self, item):
        from bzrlib.plugins.gtk.push import PushDialog
        dialog = PushDialog(self.repository, self.revids[0], self.branch)
        response = dialog.run()

        if response != gtk.RESPONSE_NONE:
            dialog.destroy()

    def show_tag(self, item):
        from bzrlib.plugins.gtk.tags import AddTagDialog
        dialog = AddTagDialog(self.repository, self.revids[0], self.branch)
        response = dialog.run()

        if response != gtk.RESPONSE_NONE:
            dialog.hide()
        
            if response == gtk.RESPONSE_OK:
                self.emit('tag-added', dialog.tagname, dialog._revid)
            
            dialog.destroy()
    
    def revert(self, item):
        pb = ui.ui_factory.nested_progress_bar()
        revision_tree = self.branch.repository.revision_tree(self.revids[0])
        try:
            self.wt.revert(old_tree = revision_tree, pb = pb)
        finally:
            pb.finished()
