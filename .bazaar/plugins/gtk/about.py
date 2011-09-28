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
import os

from bzrlib.plugins.gtk import data_path, icon_path


def read_license():
    license_paths = [data_path("COPYING"), "/usr/share/common-licenses/GPL-2"]
    for license_file in license_paths:
        if license_file is not None and os.path.exists(license_file):
            return file(license_file).read()
    # Fall back to just license name if we can't find the file
    return "GPLv2 or later"


def load_credits():
    import pickle
    try:
        credits = pickle.load(file(data_path("credits.pickle")))
    except IOError:
        credits = None
    return credits


class AboutDialog(gtk.AboutDialog):
    def __init__(self):
        super(AboutDialog, self).__init__()
        self.set_name("Bazaar GTK")
        self.set_version(bzrlib.plugins.gtk.version_string)
        self.set_website("http://bazaar-vcs.org/BzrGtk")
        self.set_license(read_license())
        self.set_logo(gtk.gdk.pixbuf_new_from_file(icon_path("bzr-icon-64.png")))
        credits = load_credits()
        if credits is not None:
            (authors, documenters, artists, translators) = credits
            self.set_authors(authors)
            self.set_documenters(documenters)
            self.set_artists(artists)
            self.set_translator_credits("\n".join(translators))
        self.connect ("response", lambda d, r: d.destroy())


