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

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import subprocess

import gtk
import gobject

from bzrlib.config import GlobalConfig
from bzrlib.plugins.gtk import _i18n

from dialog import error_dialog, warning_dialog


class ConflictsDialog(gtk.Dialog):
    """ This dialog displays the list of conflicts. """

    def __init__(self, wt, parent=None):
        """ Initialize the Conflicts dialog. """
        gtk.Dialog.__init__(self, title="Conflicts - Olive",
                                  parent=parent,
                                  flags=0,
                                  buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CANCEL))
        
        # Get arguments
        self.wt = wt
        
        # Create the widgets
        self._scrolledwindow = gtk.ScrolledWindow()
        self._treeview = gtk.TreeView()
        self._label_diff3 = gtk.Label(_i18n("External utility:"))
        self._entry_diff3 = gtk.Entry()
        self._image_diff3 = gtk.Image()
        self._button_diff3 = gtk.Button()
        self._hbox_diff3 = gtk.HBox()
        
        # Set callbacks
        self._button_diff3.connect('clicked', self._on_diff3_clicked)
        
        # Set properties
        self._scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC,
                                        gtk.POLICY_AUTOMATIC)
        self._image_diff3.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_BUTTON)
        self._button_diff3.set_image(self._image_diff3)
        self._entry_diff3.set_text(self._get_diff3())
        self._hbox_diff3.set_spacing(3)
        self.vbox.set_spacing(3)
        self.set_default_size(400, 300)
        
        # Construct dialog
        self._hbox_diff3.pack_start(self._label_diff3, False, False)
        self._hbox_diff3.pack_start(self._entry_diff3, True, True)
        self._hbox_diff3.pack_start(self._button_diff3, False, False)
        self._scrolledwindow.add(self._treeview)
        self.vbox.pack_start(self._scrolledwindow, True, True)
        self.vbox.pack_start(self._hbox_diff3, False, False)
        
        # Create the conflict list
        self._create_conflicts()
        
        # Show the dialog
        self.vbox.show_all()
    
    def _get_diff3(self):
        """ Get the specified diff3 utility. Default is meld. """
        config = GlobalConfig()
        diff3 = config.get_user_option('gconflicts_diff3')
        if diff3 is None:
            diff3 = 'meld'
        return diff3
    
    def _set_diff3(self, cmd):
        """ Set the default diff3 utility to cmd. """
        config = GlobalConfig()
        config.set_user_option('gconflicts_diff3', cmd)
    
    def _create_conflicts(self):
        """ Construct the list of conflicts. """
        if len(self.wt.conflicts()) == 0:
            self.model = gtk.ListStore(gobject.TYPE_STRING)
            self._treeview.set_model(self.model)
            self._treeview.append_column(gtk.TreeViewColumn(_i18n('Conflicts'),
                                         gtk.CellRendererText(), text=0))
            self._treeview.set_headers_visible(False)            
            self.model.append([ _i18n("No conflicts in working tree.") ])
            self._button_diff3.set_sensitive(False)
        else:
            self.model = gtk.ListStore(gobject.TYPE_STRING,
                                       gobject.TYPE_STRING,
                                       gobject.TYPE_STRING)
            self._treeview.set_model(self.model)
            self._treeview.append_column(gtk.TreeViewColumn(_i18n('Path'),
                                         gtk.CellRendererText(), text=0))
            self._treeview.append_column(gtk.TreeViewColumn(_i18n('Type'),
                                         gtk.CellRendererText(), text=1))
            self._treeview.set_search_column(0)
            for conflict in self.wt.conflicts():
                if conflict.typestring == 'path conflict':
                    t = _i18n("path conflict")
                elif conflict.typestring == 'contents conflict':
                    t = _i18n("contents conflict")
                elif conflict.typestring == 'text conflict':
                    t = _i18n("text conflict")
                elif conflict.typestring == 'duplicate id':
                    t = _i18n("duplicate id")
                elif conflict.typestring == 'duplicate':
                    t = _i18n("duplicate")
                elif conflict.typestring == 'parent loop':
                    t = _i18n("parent loop")
                elif conflict.typestring == 'unversioned parent':
                    t = _i18n("unversioned parent")
                elif conflict.typestring == 'missing parent':
                    t = _i18n("missing parent")
                elif conflict.typestring == 'deleting parent':
                    t = _i18n("deleting parent")
                else:
                    t = _i18n("unknown type of conflict")
                
                self.model.append([ conflict.path, t, conflict.typestring ]) 
    
    def _get_selected_file(self):
        """ Return the selected conflict's filename. """
        treeselection = self._treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        
        if iter is None:
            return None
        else:
            return model.get_value(iter, 0)
    
    def _get_selected_type(self):
        """ Return the type of the selected conflict. """
        treeselection = self._treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        
        if iter is None:
            return None
        else:
            return model.get_value(iter, 2)
    
    def _on_diff3_clicked(self, widget):
        """ Launch external utility to resolve conflicts. """
        self._set_diff3(self._entry_diff3.get_text())
        selected = self._get_selected_file()
        if selected is None:
            error_dialog(_i18n('No file was selected'),
                         _i18n('Please select a file from the list.'))
            return
        elif self._get_selected_type() == 'text conflict':
            base = self.wt.abspath(selected) + '.BASE'
            this = self.wt.abspath(selected) + '.THIS'
            other = self.wt.abspath(selected) + '.OTHER'
            try:
                p = subprocess.Popen([ self._entry_diff3.get_text(), base, this, other ])
                p.wait()
            except OSError, e:
                warning_dialog(_i18n('Call to external utility failed'), str(e))
        else:
            warning_dialog(_i18n('Cannot resolve conflict'),
                           _i18n('Only conflicts on the text of files can be resolved with Olive at the moment. Content conflicts, on the structure of the tree, need to be resolved using the command line.'))
            return
