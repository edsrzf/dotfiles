# Copyright (C) 2006 Szilveszter Farkas <szilveszter.farkas@gmail.com>
# Copyright (C) 2007 Jelmer Vernooij <jelmer@samba.org>

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


"""GTK UI
"""

import gtk
import sys

from bzrlib import progress
from bzrlib.ui import UIFactory


class PromptDialog(gtk.Dialog):
    """ Prompt the user for a yes/no answer. """
    def __init__(self, prompt):
        gtk.Dialog.__init__(self)

        label = gtk.Label(prompt)
        self.vbox.pack_start(label, padding=10)
        self.vbox.show_all()

        self.add_buttons(gtk.STOCK_YES, gtk.RESPONSE_YES, gtk.STOCK_NO,
                         gtk.RESPONSE_NO)


class GtkProgressBar(gtk.ProgressBar):

    def __init__(self):
        gtk.ProgressBar.__init__(self)
        self.set_fraction(0.0)
        self.current = None
        self.total = None

    def tick(self):
        self.show()
        self.pulse()

    def update(self, msg=None, current_cnt=None, total_cnt=None):
        self.show()
        if current_cnt is not None:
            self.current = current_cnt
        if total_cnt is not None:
            self.total = total_cnt
        if msg is not None:
            self.set_text(msg)
        if None not in (self.current, self.total):
            self.fraction = float(self.current) / self.total
            if self.fraction < 0.0 or self.fraction > 1.0:
                raise AssertionError
            self.set_fraction(self.fraction)
        while gtk.events_pending():
            gtk.main_iteration()

    def finished(self):
        self.hide()

    def clear(self):
        self.hide()


class ProgressBarWindow(gtk.Window):

    def __init__(self):
        super(ProgressBarWindow, self).__init__(type=gtk.WINDOW_TOPLEVEL)
        self.set_border_width(0)
        self.set_title("Progress")
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.pb = GtkProgressBar()
        self.add(self.pb)
        self.resize(250, 15)
        self.set_resizable(False)

    def tick(self, *args, **kwargs):
        self.show_all()
        self.pb.tick(*args, **kwargs)

    def update(self, *args, **kwargs):
        self.show_all()
        self.pb.update(*args, **kwargs)

    def finished(self):
        self.pb.finished()
        self.hide_all()
        self.destroy()

    def clear(self):
        self.pb.clear()
        self.hide_all()


class ProgressPanel(gtk.HBox):

    def __init__(self):
        super(ProgressPanel, self).__init__()
        image_loading = gtk.image_new_from_stock(gtk.STOCK_REFRESH,
                                                 gtk.ICON_SIZE_BUTTON)
        image_loading.show()

        self.pb = GtkProgressBar()
        self.set_spacing(5)
        self.set_border_width(5)
        self.pack_start(image_loading, False, False)
        self.pack_start(self.pb, True, True)

    def tick(self, *args, **kwargs):
        self.show_all()
        self.pb.tick(*args, **kwargs)

    def update(self, *args, **kwargs):
        self.show_all()
        self.pb.update(*args, **kwargs)

    def finished(self):
        self.pb.finished()
        self.hide_all()

    def clear(self):
        self.pb.clear()
        self.hide_all()


class PasswordDialog(gtk.Dialog):
    """ Prompt the user for a password. """

    def __init__(self, prompt):
        gtk.Dialog.__init__(self)

        label = gtk.Label(prompt)
        self.vbox.pack_start(label, padding=10)

        self.entry = gtk.Entry()
        self.entry.set_visibility(False)
        self.vbox.pack_end(self.entry, padding=10)

        self.vbox.show_all()

        self.add_buttons(gtk.STOCK_OK, gtk.RESPONSE_OK,
                         gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)

    def _get_passwd(self):
        return self.entry.get_text()

    passwd = property(_get_passwd)


class GtkUIFactory(UIFactory):
    """A UI factory for GTK user interfaces."""

    def __init__(self):
        """Create a GtkUIFactory"""
        super(GtkUIFactory, self).__init__()
        self.set_progress_bar_widget(None)

    def set_progress_bar_widget(self, widget):
        self._progress_bar_widget = widget

    def get_boolean(self, prompt):
        """GtkDialog with yes/no answers"""
        dialog = PromptDialog(prompt)
        response = dialog.run()
        dialog.destroy()
        return (response == gtk.RESPONSE_YES)

    def get_password(self, prompt='', **kwargs):
        """Prompt the user for a password.

        :param prompt: The prompt to present the user
        :param kwargs: Arguments which will be expanded into the prompt.
                       This lets front ends display different things if
                       they so choose.
        :return: The password string, return None if the user 
                 canceled the request.
        """
        dialog = PasswordDialog(prompt % kwargs)
        response = dialog.run()
        passwd = dialog.passwd
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            return passwd
        else:
            return None

    def _progress_all_finished(self):
        """See UIFactory._progress_all_finished"""
        pbw = self._progress_bar_widget
        if pbw:
            pbw.finished()

    def _progress_updated(self, task):
        """See UIFactory._progress_updated"""
        if self._progress_bar_widget is None:
            # Default to a window since nobody gave us a better mean to report
            # progress.
            self.set_progress_bar_widget(ProgressBarWindow())
        self._progress_bar_widget.update(task.msg,
                                         task.current_cnt, task.total_cnt)

