# Copyright (C) 2007 by Robert Collins
#                       Jelmer Vernooij
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""Notification area icon and notification for Bazaar."""

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import gtk
import bzrlib


def has_dbus():
    return (getattr(bzrlib.plugins, "dbus", None) is not None)


def has_avahi():
    return (getattr(bzrlib.plugins, "avahi", None) is not None)


class NotifyPopupMenu(gtk.Menu):

    def __init__(self):
        super(NotifyPopupMenu, self).__init__()
        self.create_items()

    def create_items(self):
        from bzrlib import errors
        item = gtk.CheckMenuItem('_Gateway to LAN')
        item.connect('toggled', self.toggle_lan_gateway)
        self.append(item)
        self.append(gtk.SeparatorMenuItem())
        try:
            from bzrlib.plugins.dbus.activity import LanGateway
            self.langateway = LanGateway()
        except ImportError:
            item.set_sensitive(False)
        except errors.BzrError:
            # FIXME: Should only catch errors that indicate a lan-notify 
            # process is already running.
            item.set_sensitive(False)

        item = gtk.CheckMenuItem('Announce _branches on LAN')
        item.connect('toggled', self.toggle_announce_branches)
        self.append(item)
        self.append(gtk.SeparatorMenuItem())
        try:
            from bzrlib.plugins.avahi.share import ZeroConfServer
            from bzrlib import urlutils
            self.zeroconfserver = ZeroConfServer(urlutils.normalize_url('.'))
        except ImportError:
            item.set_sensitive(False)

        item = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES, None)
        item.connect('activate', self.show_preferences)
        self.append(item)
        item = gtk.ImageMenuItem(gtk.STOCK_ABOUT, None)
        item.connect('activate', self.show_about)
        self.append(item)
        self.append(gtk.SeparatorMenuItem())
        item = gtk.ImageMenuItem(gtk.STOCK_QUIT, None)
        item.connect('activate', gtk.main_quit)
        self.append(item)
        self.show_all()

    def display(self, icon, event_button, event_time):
        self.popup(None, None, gtk.status_icon_position_menu, 
               event_button, event_time, icon)

    def toggle_lan_gateway(self, item):
        if item.get_active():
            self.langateway.start()
        else:
            self.langateway.stop()

    def toggle_announce_branches(self, item):
        if item.get_active():
            self.zeroconfserver.start()
        else:
            self.zeroconfserver.close()

    def show_about(self, item):
        from bzrlib.plugins.gtk.about import AboutDialog
        dialog = AboutDialog()
        dialog.run()

    def show_preferences(self, item):
        from bzrlib.plugins.gtk.preferences import PreferencesWindow
        prefs = PreferencesWindow()
        prefs.run()

