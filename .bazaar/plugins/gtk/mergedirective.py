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

import bzrlib
import gtk

from bzrlib.plugins.gtk.branchbox import BranchSelectionBox

class CreateMergeDirectiveDialog(gtk.Dialog):
    def __init__(self, branch, stop_revid=None):
        super(CreateMergeDirectiveDialog, self).__init__()
        self.branch = branch
        self.stop_revid = stop_revid
        self._create()

    def _create(self):
        # TODO: Create a frame with information about the revision that will be 
        # submittted

        # TODO: Create a frame with a the ability to select a branch
        
        # TODO: Create a frame with a button for selecting a file name 
        # for the bundle
        pass


class SendMergeDirectiveDialog(gtk.Dialog):
    def __init__(self, branch, parent=None):
        super(SendMergeDirectiveDialog, self).__init__(parent)
        self.branch = branch
        self.set_title("Send Merge Directive")
        self._create()

    def _create(self):
        table = gtk.Table(rows=3, columns=2)
        self.vbox.add(table)

        label = gtk.Label()
        label.set_markup("<b>Branch to Submit:</b>")
        table.attach(label, 0, 1, 0, 1, gtk.FILL, gtk.FILL)

        label = gtk.Label(str(self.branch))
        table.attach(label, 1, 2, 0, 1, gtk.FILL, gtk.FILL)

        label = gtk.Label()
        label.set_markup("<b>Target Branch:</b>")
        table.attach(label, 0, 1, 1, 2, gtk.FILL, gtk.FILL)

        self.submit_branch = BranchSelectionBox(self.branch.get_submit_branch())
        table.attach(self.submit_branch, 1, 2, 1, 2, gtk.FILL, gtk.FILL)

        # TODO: Display number of revisions to be send whenever 
        # submit branch changes

        label = gtk.Label()
        label.set_markup("<b>Email To:</b>")
        table.attach(label, 0, 1, 2, 3, gtk.FILL, gtk.FILL)

        self.mail_to = gtk.ComboBoxEntry()
        mail_to = self.branch.get_config().get_user_option('submit_to')
        if mail_to is None:
            submit_branch = self.submit_branch.get_branch()
            if submit_branch is not None:
                mail_to = submit_branch.get_config().get_user_option(
                            'child_submit_to')
        if mail_to is not None:
            self.mail_to.get_child().set_text(mail_to)
        table.attach(self.mail_to, 1, 2, 2, 3, gtk.FILL, gtk.FILL)

        self.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
                         gtk.STOCK_OK, gtk.RESPONSE_OK)

        self.show_all()

    def get_mail_to(self):
        return self.mail_to.get_child().get_text()

    def get_merge_directive(self):
        from bzrlib.merge_directive import MergeDirective2
        from bzrlib import osutils
        import time
        return MergeDirective2.from_objects(self.branch.repository,
                                            self.branch.last_revision(),
                                            time.time(),
                                            osutils.local_time_offset(),
                                            self.submit_branch.get_url(),
                                            public_branch=None,
                                            include_patch=True,
                                            include_bundle=True,
                                            message=None,
                                            base_revision_id=None)



class ApplyMergeDirectiveDialog(gtk.Dialog):
    def __init__(self):
        super(ApplyMergeDirectiveDialog, self).__init__()
