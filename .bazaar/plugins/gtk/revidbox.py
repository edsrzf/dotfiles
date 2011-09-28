# Copyright (C) 2007 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
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

class RevisionSelectionBox(gtk.HBox):
    def __init__(self, branch):
        super(RevisionSelectionBox, self).__init__()
        self._branch = branch
        self._entry_revid = gtk.Entry()
        self._button_revid = gtk.Button('')
        self._button_revid.set_image(gtk.image_new_from_stock(
            gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON))
        self.pack_start(self._entry_revid, True, True)
        self.pack_start(self._button_revid, False, False) 

        self._button_revid.connect('clicked', self._on_revid_clicked)

    def _on_revid_clicked(self, widget):
        """ Browse for revision button clicked handler. """
        from revbrowser import RevisionBrowser
        
        # FIXME: Should specific parent window here - how to get to it?
        # JRV 20070715
        revb = RevisionBrowser(self._branch)
        response = revb.run()
        if response != gtk.RESPONSE_NONE:
            revb.hide()
        
            if response == gtk.RESPONSE_OK:
                if revb.selected_revno is not None:
                    self._entry_revid.set_text(revb.selected_revid)
            
            revb.destroy()

    def get_revision_id(self):
        if len(self._entry_revid.get_text()) == 0:
            return None
        else:
            return self._entry_revid.get_text()
