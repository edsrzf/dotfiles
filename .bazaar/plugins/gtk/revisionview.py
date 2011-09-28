# Copyright (C) 2005 Dan Loda <danloda@gmail.com>
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

import pygtk
pygtk.require("2.0")
import gtk
import pango
import gobject
import webbrowser

from bzrlib import trace
from bzrlib.osutils import format_date
try:
    from bzrlib.bencode import bdecode
except ImportError:
    from bzrlib.util.bencode import bdecode
from bzrlib.testament import Testament

from bzrlib.plugins.gtk import icon_path

try:
    from bzrlib.plugins.gtk import seahorse
except ImportError:
    has_seahorse = False
else:
    has_seahorse = True

PAGE_GENERAL = 0
PAGE_RELATIONS = 1
PAGE_SIGNATURE = 2
PAGE_BUGS = 3


def _open_link(widget, uri):
    for cmd in ['sensible-browser', 'xdg-open']:
        if webbrowser._iscommand(cmd):
            webbrowser._tryorder.insert(0, '%s "%%s"' % cmd)
    webbrowser.open(uri)

if getattr(gtk, 'link_button_set_uri_hook', None) is not None:
    # Not available before PyGtk-2.10
    gtk.link_button_set_uri_hook(_open_link)

class BugsTab(gtk.VBox):

    def __init__(self):
        super(BugsTab, self).__init__(False, 6)

        table = gtk.Table(rows=2, columns=2)

        table.set_row_spacings(6)
        table.set_col_spacing(0, 16)

        image = gtk.Image()
        image.set_from_file(icon_path("bug.png"))
        table.attach(image, 0, 1, 0, 1, gtk.FILL)

        align = gtk.Alignment(0.0, 0.1)
        self.label = gtk.Label()
        align.add(self.label)
        table.attach(align, 1, 2, 0, 1, gtk.FILL)

        treeview = self.construct_treeview()
        table.attach(treeview, 1, 2, 1, 2, gtk.FILL | gtk.EXPAND)

        self.set_border_width(6)
        self.pack_start(table, expand=False)

        self.clear()
        self.show_all()

    def set_revision(self, revision):
        if revision is None:
            return

        self.clear()
        bugs_text = revision.properties.get('bugs', '')
        for bugline in bugs_text.splitlines():
                (url, status) = bugline.split(" ")
                if status == "fixed":
                    self.add_bug(url, status)
        
        if self.num_bugs == 0:
            return
        elif self.num_bugs == 1:
            label = "bug"
        else:
            label = "bugs"

        self.label.set_markup("<b>Bugs fixed</b>\n" +
                              "This revision claims to fix " +
                              "%d %s." % (self.num_bugs, label))

    def construct_treeview(self):
        self.bugs = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.treeview = gtk.TreeView(self.bugs)
        self.treeview.set_headers_visible(False)

        uri_column = gtk.TreeViewColumn('Bug URI', gtk.CellRendererText(), text=0)
        self.treeview.append_column(uri_column)

        self.treeview.connect('row-activated', self.on_row_activated)

        win = gtk.ScrolledWindow()
        win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        win.set_shadow_type(gtk.SHADOW_IN)
        win.add(self.treeview)

        return win

    def clear(self):
        self.num_bugs = 0
        self.bugs.clear()
        self.set_sensitive(False)
        self.label.set_markup("<b>No bugs fixed</b>\n" +
                              "This revision does not claim to fix any bugs.")

    def add_bug(self, url, status):
        self.num_bugs += 1
        self.bugs.append([url, status])
        self.set_sensitive(True)

    def get_num_bugs(self):
        return self.num_bugs

    def on_row_activated(self, treeview, path, column):
        uri = self.bugs.get_value(self.bugs.get_iter(path), 0)
        _open_link(self, uri)


class SignatureTab(gtk.VBox):

    def __init__(self, repository):
        self.key = None
        self.revision = None
        self.repository = repository

        super(SignatureTab, self).__init__(False, 6)
        signature_box = gtk.Table(rows=3, columns=3)
        signature_box.set_col_spacing(0, 16)
        signature_box.set_col_spacing(1, 12)
        signature_box.set_row_spacings(6)

        self.signature_image = gtk.Image()
        signature_box.attach(self.signature_image, 0, 1, 0, 1, gtk.FILL)

        align = gtk.Alignment(0.0, 0.1)
        self.signature_label = gtk.Label()
        align.add(self.signature_label)
        signature_box.attach(align, 1, 3, 0, 1, gtk.FILL)

        align = gtk.Alignment(0.0, 0.5)
        self.signature_key_id_label = gtk.Label()
        self.signature_key_id_label.set_markup("<b>Key Id:</b>")
        align.add(self.signature_key_id_label)
        signature_box.attach(align, 1, 2, 1, 2, gtk.FILL, gtk.FILL)

        align = gtk.Alignment(0.0, 0.5)
        self.signature_key_id = gtk.Label()
        self.signature_key_id.set_selectable(True)
        align.add(self.signature_key_id)
        signature_box.attach(align, 2, 3, 1, 2, gtk.EXPAND | gtk.FILL, gtk.FILL)

        align = gtk.Alignment(0.0, 0.5)
        self.signature_fingerprint_label = gtk.Label()
        self.signature_fingerprint_label.set_markup("<b>Fingerprint:</b>")
        align.add(self.signature_fingerprint_label)
        signature_box.attach(align, 1, 2, 2, 3, gtk.FILL, gtk.FILL)

        align = gtk.Alignment(0.0, 0.5)
        self.signature_fingerprint = gtk.Label()
        self.signature_fingerprint.set_selectable(True)
        align.add(self.signature_fingerprint)
        signature_box.attach(align, 2, 3, 2, 3, gtk.EXPAND | gtk.FILL, gtk.FILL)

        align = gtk.Alignment(0.0, 0.5)
        self.signature_trust_label = gtk.Label()
        self.signature_trust_label.set_markup("<b>Trust:</b>")
        align.add(self.signature_trust_label)
        signature_box.attach(align, 1, 2, 3, 4, gtk.FILL, gtk.FILL)

        align = gtk.Alignment(0.0, 0.5)
        self.signature_trust = gtk.Label()
        self.signature_trust.set_selectable(True)
        align.add(self.signature_trust)
        signature_box.attach(align, 2, 3, 3, 4, gtk.EXPAND | gtk.FILL, gtk.FILL)

        self.set_border_width(6)
        self.pack_start(signature_box, expand=False)
        self.show_all()

    def set_revision(self, revision):
        self.revision = revision
        revid = revision.revision_id

        if self.repository.has_signature_for_revision_id(revid):
            crypttext = self.repository.get_signature_text(revid)
            self.show_signature(crypttext)
        else:
            self.show_no_signature()

    def show_no_signature(self):
        self.signature_key_id_label.hide()
        self.signature_key_id.set_text("")

        self.signature_fingerprint_label.hide()
        self.signature_fingerprint.set_text("")

        self.signature_trust_label.hide()
        self.signature_trust.set_text("")

        self.signature_image.set_from_file(icon_path("sign-unknown.png"))
        self.signature_label.set_markup("<b>Authenticity unknown</b>\n" +
                                        "This revision has not been signed.")

    def show_signature(self, crypttext):
        (cleartext, key) = seahorse.verify(crypttext)

        assert cleartext is not None

        inv = self.repository.get_inventory(self.revision.revision_id)
        expected_testament = Testament(self.revision, inv).as_short_text()
        if expected_testament != cleartext:
            self.signature_image.set_from_file(icon_path("sign-bad.png"))
            self.signature_label.set_markup("<b>Signature does not match repository data</b>\n" +
                        "The signature plaintext is different from the expected testament plaintext.")
            return

        if key and key.is_available():
            if key.is_trusted():
                if key.get_display_name() == self.revision.committer:
                    self.signature_image.set_from_file(icon_path("sign-ok.png"))
                    self.signature_label.set_markup("<b>Authenticity confirmed</b>\n" +
                                                    "This revision has been signed with " +
                                                    "a trusted key.")
                else:
                    self.signature_image.set_from_file(icon_path("sign-bad.png"))
                    self.signature_label.set_markup("<b>Authenticity cannot be confirmed</b>\n" +
                                                    "Revision committer is not the same as signer.")
            else:
                self.signature_image.set_from_file(icon_path("sign-bad.png"))
                self.signature_label.set_markup("<b>Authenticity cannot be confirmed</b>\n" +
                                                "This revision has been signed, but the " +
                                                "key is not trusted.")
        else:
            self.show_no_signature()
            self.signature_image.set_from_file(icon_path("sign-bad.png"))
            self.signature_label.set_markup("<b>Authenticity cannot be confirmed</b>\n" +
                                            "Signature key not available.")
            return

        trust = key.get_trust()

        if trust <= seahorse.TRUST_NEVER:
            trust_text = 'never trusted'
        elif trust == seahorse.TRUST_UNKNOWN:
            trust_text = 'not trusted'
        elif trust == seahorse.TRUST_MARGINAL:
            trust_text = 'marginally trusted'
        elif trust == seahorse.TRUST_FULL:
            trust_text = 'fully trusted'
        elif trust == seahorse.TRUST_ULTIMATE:
            trust_text = 'ultimately trusted'

        self.signature_key_id_label.show()
        self.signature_key_id.set_text(key.get_id())

        fingerprint = key.get_fingerprint()
        if fingerprint == "":
            fingerprint = '<span foreground="dim grey">N/A</span>'

        self.signature_fingerprint_label.show()
        self.signature_fingerprint.set_markup(fingerprint)

        self.signature_trust_label.show()
        self.signature_trust.set_text('This key is ' + trust_text)


class RevisionView(gtk.Notebook):
    """ Custom widget for commit log details.

    A variety of bzr tools may need to implement such a thing. This is a
    start.
    """

    __gproperties__ = {
        'branch': (
            gobject.TYPE_PYOBJECT,
            'Branch',
            'The branch holding the revision being displayed',
            gobject.PARAM_CONSTRUCT_ONLY | gobject.PARAM_WRITABLE
        ),

        'revision': (
            gobject.TYPE_PYOBJECT,
            'Revision',
            'The revision being displayed',
            gobject.PARAM_READWRITE
        ),

        'children': (
            gobject.TYPE_PYOBJECT,
            'Children',
            'Child revisions',
            gobject.PARAM_READWRITE
        ),

        'file-id': (
            gobject.TYPE_PYOBJECT,
            'File Id',
            'The file id',
            gobject.PARAM_READWRITE
        )
    }

    def __init__(self, branch=None, repository=None):
        gtk.Notebook.__init__(self)

        self._revision = None
        self._branch = branch
        if branch is not None:
            self._repository = branch.repository
        else:
            self._repository = repository

        self._create_general()
        self._create_relations()
        # Disabled because testaments aren't verified yet:
        if has_seahorse:
            self._create_signature()
        self._create_file_info_view()
        self._create_bugs()

        self.set_current_page(PAGE_GENERAL)
        self.connect_after('switch-page', self._switch_page_cb)
        
        self._show_callback = None
        self._clicked_callback = None

        self._revision = None
        self._branch = branch

        self.update_tags()

        self.set_file_id(None)

    def do_get_property(self, property):
        if property.name == 'branch':
            return self._branch
        elif property.name == 'revision':
            return self._revision
        elif property.name == 'children':
            return self._children
        elif property.name == 'file-id':
            return self._file_id
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def do_set_property(self, property, value):
        if property.name == 'branch':
            self._branch = value
        elif property.name == 'revision':
            self._set_revision(value)
        elif property.name == 'children':
            self.set_children(value)
        elif property.name == 'file-id':
            self._file_id = value
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def set_show_callback(self, callback):
        self._show_callback = callback

    def set_file_id(self, file_id):
        """Set a specific file id that we want to track.

        This just effects the display of a per-file commit message.
        If it is set to None, then all commit messages will be shown.
        """
        self.set_property('file-id', file_id)

    def set_revision(self, revision):
        if revision != self._revision:
            self.set_property('revision', revision)

    def get_revision(self):
        return self.get_property('revision')

    def _set_revision(self, revision):
        if revision is None: return

        self._revision = revision
        if revision.committer is not None:
            self.committer.set_text(revision.committer)
        else:
            self.committer.set_text("")
        author = revision.properties.get('author', '')
        if author != '':
            self.author.set_text(author)
            self.author.show()
            self.author_label.show()
        else:
            self.author.hide()
            self.author_label.hide()

        if revision.timestamp is not None:
            self.timestamp.set_text(format_date(revision.timestamp,
                                                revision.timezone))
        try:
            self.branchnick.show()
            self.branchnick_label.show()
            self.branchnick.set_text(revision.properties['branch-nick'])
        except KeyError:
            self.branchnick.hide()
            self.branchnick_label.hide()

        self._add_parents_or_children(revision.parent_ids,
                                      self.parents_widgets,
                                      self.parents_table)

        file_info = revision.properties.get('file-info', None)
        if file_info is not None:
            try:
                file_info = bdecode(file_info.encode('UTF-8'))
            except ValueError:
                trace.note('Invalid per-file info for revision:%s, value: %r',
                           revision.revision_id, file_info)
                file_info = None

        if file_info:
            if self._file_id is None:
                text = []
                for fi in file_info:
                    text.append('%(path)s\n%(message)s' % fi)
                self.file_info_buffer.set_text('\n'.join(text))
                self.file_info_box.show()
            else:
                text = []
                for fi in file_info:
                    if fi['file_id'] == self._file_id:
                        text.append(fi['message'])
                if text:
                    self.file_info_buffer.set_text('\n'.join(text))
                    self.file_info_box.show()
                else:
                    self.file_info_box.hide()
        else:
            self.file_info_box.hide()

    def update_tags(self):
        if self._branch is not None and self._branch.supports_tags():
            self._tagdict = self._branch.tags.get_reverse_tag_dict()
        else:
            self._tagdict = {}

        self._add_tags()

    def _update_signature(self, widget, param):
        if self.get_current_page() == PAGE_SIGNATURE:
            self.signature_table.set_revision(self._revision)

    def _update_bugs(self, widget, param):
        self.bugs_page.set_revision(self._revision)
        label = self.get_tab_label(self.bugs_page)
        label.set_sensitive(self.bugs_page.get_num_bugs() != 0)

    def set_children(self, children):
        self._add_parents_or_children(children,
                                      self.children_widgets,
                                      self.children_table)

    def _switch_page_cb(self, notebook, page, page_num):
        if page_num == PAGE_SIGNATURE:
            self.signature_table.set_revision(self._revision)



    def _show_clicked_cb(self, widget, revid, parentid):
        """Callback for when the show button for a parent is clicked."""
        self._show_callback(revid, parentid)

    def _go_clicked_cb(self, widget, revid):
        """Callback for when the go button for a parent is clicked."""

    def _add_tags(self, *args):
        if self._revision is None:
            return

        if self._tagdict.has_key(self._revision.revision_id):
            tags = self._tagdict[self._revision.revision_id]
        else:
            tags = []
            
        if tags == []:
            self.tags_list.hide()
            self.tags_label.hide()
            return

        self.tags_list.set_text(", ".join(tags))

        self.tags_list.show_all()
        self.tags_label.show_all()
        
    def _add_parents_or_children(self, revids, widgets, table):
        while len(widgets) > 0:
            widget = widgets.pop()
            table.remove(widget)
        
        table.resize(max(len(revids), 1), 2)

        for idx, revid in enumerate(revids):
            align = gtk.Alignment(0.0, 0.0, 1, 1)
            widgets.append(align)
            table.attach(align, 1, 2, idx, idx + 1,
                                      gtk.EXPAND | gtk.FILL, gtk.FILL)
            align.show()

            hbox = gtk.HBox(False, spacing=6)
            align.add(hbox)
            hbox.show()

            image = gtk.Image()
            image.set_from_stock(
                gtk.STOCK_FIND, gtk.ICON_SIZE_SMALL_TOOLBAR)
            image.show()

            if self._show_callback is not None:
                button = gtk.Button()
                button.add(image)
                button.connect("clicked", self._show_clicked_cb,
                               self._revision.revision_id, revid)
                hbox.pack_start(button, expand=False, fill=True)
                button.show()

            button = gtk.Button()
            revid_label = gtk.Label(str(revid))
            revid_label.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
            revid_label.set_alignment(0.0, 0.5)
            button.add(revid_label)
            button.connect("clicked",
                    lambda w, r: self.set_revision(self._repository.get_revision(r)), revid)
            button.set_use_underline(False)
            hbox.pack_start(button, expand=True, fill=True)
            button.show_all()

    def _create_general(self):
        vbox = gtk.VBox(False, 6)
        vbox.set_border_width(6)
        vbox.pack_start(self._create_headers(), expand=False, fill=True)
        vbox.pack_start(self._create_message_view())
        self.append_page(vbox, tab_label=gtk.Label("General"))
        vbox.show()

    def _create_relations(self):
        vbox = gtk.VBox(False, 6)
        vbox.set_border_width(6)
        vbox.pack_start(self._create_parents(), expand=False, fill=True)
        vbox.pack_start(self._create_children(), expand=False, fill=True)
        self.append_page(vbox, tab_label=gtk.Label("Relations"))
        vbox.show()

    def _create_signature(self):
        self.signature_table = SignatureTab(self._repository)
        self.append_page(self.signature_table, tab_label=gtk.Label('Signature'))
        self.connect_after('notify::revision', self._update_signature)

    def _create_headers(self):
        self.table = gtk.Table(rows=5, columns=2)
        self.table.set_row_spacings(6)
        self.table.set_col_spacings(6)
        self.table.show()

        row = 0

        label = gtk.Label()
        label.set_alignment(1.0, 0.5)
        label.set_markup("<b>Revision Id:</b>")
        self.table.attach(label, 0, 1, row, row+1, gtk.FILL, gtk.FILL)
        label.show()

        revision_id = gtk.Label()
        revision_id.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
        revision_id.set_alignment(0.0, 0.5)
        revision_id.set_selectable(True)
        self.connect('notify::revision', 
                lambda w, p: revision_id.set_text(self._revision.revision_id))
        self.table.attach(revision_id, 1, 2, row, row+1, gtk.EXPAND | gtk.FILL, gtk.FILL)
        revision_id.show()

        row += 1
        self.author_label = gtk.Label()
        self.author_label.set_alignment(1.0, 0.5)
        self.author_label.set_markup("<b>Author:</b>")
        self.table.attach(self.author_label, 0, 1, row, row+1, gtk.FILL, gtk.FILL)
        self.author_label.show()

        self.author = gtk.Label()
        self.author.set_ellipsize(pango.ELLIPSIZE_END)
        self.author.set_alignment(0.0, 0.5)
        self.author.set_selectable(True)
        self.table.attach(self.author, 1, 2, row, row+1, gtk.EXPAND | gtk.FILL, gtk.FILL)
        self.author.show()
        self.author.hide()

        row += 1
        label = gtk.Label()
        label.set_alignment(1.0, 0.5)
        label.set_markup("<b>Committer:</b>")
        self.table.attach(label, 0, 1, row, row+1, gtk.FILL, gtk.FILL)
        label.show()

        self.committer = gtk.Label()
        self.committer.set_ellipsize(pango.ELLIPSIZE_END)
        self.committer.set_alignment(0.0, 0.5)
        self.committer.set_selectable(True)
        self.table.attach(self.committer, 1, 2, row, row+1, gtk.EXPAND | gtk.FILL, gtk.FILL)
        self.committer.show()

        row += 1
        self.branchnick_label = gtk.Label()
        self.branchnick_label.set_alignment(1.0, 0.5)
        self.branchnick_label.set_markup("<b>Branch nick:</b>")
        self.table.attach(self.branchnick_label, 0, 1, row, row+1, gtk.FILL, gtk.FILL)
        self.branchnick_label.show()

        self.branchnick = gtk.Label()
        self.branchnick.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
        self.branchnick.set_alignment(0.0, 0.5)
        self.branchnick.set_selectable(True)
        self.table.attach(self.branchnick, 1, 2, row, row+1, gtk.EXPAND | gtk.FILL, gtk.FILL)
        self.branchnick.show()

        row += 1
        label = gtk.Label()
        label.set_alignment(1.0, 0.5)
        label.set_markup("<b>Timestamp:</b>")
        self.table.attach(label, 0, 1, row, row+1, gtk.FILL, gtk.FILL)
        label.show()

        self.timestamp = gtk.Label()
        self.timestamp.set_ellipsize(pango.ELLIPSIZE_END)
        self.timestamp.set_alignment(0.0, 0.5)
        self.timestamp.set_selectable(True)
        self.table.attach(self.timestamp, 1, 2, row, row+1, gtk.EXPAND | gtk.FILL, gtk.FILL)
        self.timestamp.show()

        row += 1
        self.tags_label = gtk.Label()
        self.tags_label.set_alignment(1.0, 0.5)
        self.tags_label.set_markup("<b>Tags:</b>")
        self.table.attach(self.tags_label, 0, 1, row, row+1, gtk.FILL, gtk.FILL)
        self.tags_label.show()

        self.tags_list = gtk.Label()
        self.tags_list.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
        self.tags_list.set_alignment(0.0, 0.5)
        self.table.attach(self.tags_list, 1, 2, row, row+1, gtk.EXPAND | gtk.FILL, gtk.FILL)
        self.tags_list.show()

        self.connect('notify::revision', self._add_tags)

        return self.table
    
    def _create_parents(self):
        hbox = gtk.HBox(True, 3)
        
        self.parents_table = self._create_parents_or_children_table(
            "<b>Parents:</b>")
        self.parents_widgets = []
        hbox.pack_start(self.parents_table)

        hbox.show()
        return hbox

    def _create_children(self):
        hbox = gtk.HBox(True, 3)
        self.children_table = self._create_parents_or_children_table(
            "<b>Children:</b>")
        self.children_widgets = []
        hbox.pack_start(self.children_table)
        hbox.show()
        return hbox
        
    def _create_parents_or_children_table(self, text):
        table = gtk.Table(rows=1, columns=2)
        table.set_row_spacings(3)
        table.set_col_spacings(6)
        table.show()

        label = gtk.Label()
        label.set_markup(text)
        align = gtk.Alignment(0.0, 0.5)
        align.add(label)
        table.attach(align, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        label.show()
        align.show()

        return table

    def _create_message_view(self):
        msg_buffer = gtk.TextBuffer()
        self.connect('notify::revision',
                lambda w, p: msg_buffer.set_text(self._revision.message))
        window = gtk.ScrolledWindow()
        window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        window.set_shadow_type(gtk.SHADOW_IN)
        tv = gtk.TextView(msg_buffer)
        tv.set_editable(False)
        tv.set_wrap_mode(gtk.WRAP_WORD)

        tv.modify_font(pango.FontDescription("Monospace"))
        tv.show()
        window.add(tv)
        window.show()
        return window

    def _create_bugs(self):
        self.bugs_page = BugsTab()
        self.connect_after('notify::revision', self._update_bugs) 
        self.append_page(self.bugs_page, tab_label=gtk.Label('Bugs'))

    def _create_file_info_view(self):
        self.file_info_box = gtk.VBox(False, 6)
        self.file_info_box.set_border_width(6)
        self.file_info_buffer = gtk.TextBuffer()
        window = gtk.ScrolledWindow()
        window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        window.set_shadow_type(gtk.SHADOW_IN)
        tv = gtk.TextView(self.file_info_buffer)
        tv.set_editable(False)
        tv.set_wrap_mode(gtk.WRAP_WORD)
        tv.modify_font(pango.FontDescription("Monospace"))
        tv.show()
        window.add(tv)
        window.show()
        self.file_info_box.pack_start(window)
        self.file_info_box.hide() # Only shown when there are per-file messages
        self.append_page(self.file_info_box, tab_label=gtk.Label('Per-file'))

