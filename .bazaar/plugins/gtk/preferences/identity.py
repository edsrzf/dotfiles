# Copyright (C) 2007-2008 Jelmer Vernooij <jelmer@samba.org>
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

class IdentityPage(gtk.Table):

    def __init__(self, config):
        self.config = config
        gtk.Table.__init__(self, rows=4, columns=2)
        self.set_border_width(12)
        self.set_row_spacings(6)
        self.set_col_spacings(6)

        align = gtk.Alignment(0.0, 0.5)
        label = gtk.Label()
        label.set_markup("E-Mail:")
        align.add(label)
        self.attach(align, 0, 1, 0, 1, gtk.FILL, gtk.FILL)

        self.username = gtk.Entry()
        self.username.set_text(self.config.username())
        self.attach(self.username, 1, 2, 0, 1, gtk.EXPAND | gtk.FILL, gtk.FILL)

        align = gtk.Alignment(0.0, 0.5)
        label = gtk.Label()
        label.set_markup("GPG signing command:")
        align.add(label)
        self.attach(align, 0, 1, 1, 2, gtk.FILL, gtk.FILL)

        self.email = gtk.Entry()
        self.email.set_text(self.config.gpg_signing_command())
        self.attach(self.email, 1, 2, 1, 2, gtk.EXPAND | gtk.FILL, gtk.FILL)

        align = gtk.Alignment(0.0, 0.1)
        label = gtk.Label()
        label.set_markup("Check GPG Signatures:")
        align.add(label)
        self.attach(align, 0, 1, 2, 3, gtk.FILL, gtk.FILL)

        sigvals = gtk.VBox()
        self.check_sigs_if_possible = gtk.RadioButton(None, 
                                                      "_Check if possible")
        sigvals.pack_start(self.check_sigs_if_possible)
        self.check_sigs_always = gtk.RadioButton(self.check_sigs_if_possible, 
                                                 "Check _always")
        sigvals.pack_start(self.check_sigs_always)
        self.check_sigs_never = gtk.RadioButton(self.check_sigs_if_possible,
                                                "Check _never")
        sigvals.pack_start(self.check_sigs_never)
        # FIXME: Set default
        self.attach(sigvals, 1, 2, 2, 3, gtk.EXPAND | gtk.FILL, gtk.FILL)

        align = gtk.Alignment(0.0, 0.1)
        label = gtk.Label()
        label.set_markup("Create GPG Signatures:")
        align.add(label)
        self.attach(align, 0, 1, 3, 4, gtk.FILL, gtk.FILL)

        create_sigs = gtk.VBox()
        self.create_sigs_when_required = gtk.RadioButton(None, 
                                                         "Sign When _Required")
        create_sigs.pack_start(self.create_sigs_when_required)
        self.create_sigs_always = gtk.RadioButton(
            self.create_sigs_when_required, "Sign _Always")
        create_sigs.pack_start(self.create_sigs_always)
        self.create_sigs_never = gtk.RadioButton(
            self.create_sigs_when_required, "Sign _Never")
        create_sigs.pack_start(self.create_sigs_never)
        # FIXME: Set default
        self.attach(create_sigs, 1, 2, 3, 4, gtk.EXPAND | gtk.FILL, gtk.FILL)
