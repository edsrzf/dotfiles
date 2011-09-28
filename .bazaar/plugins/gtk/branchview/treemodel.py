# -*- coding: UTF-8 -*-
"""Tree model.

"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Gary van der Merwe <garyvdm@gmail.com>"


import gtk
import gobject
import re
from xml.sax.saxutils import escape

from bzrlib.config import parse_username
from bzrlib.revision import NULL_REVISION

from time import (strftime, localtime)

REVID = 0
NODE = 1
LINES = 2
LAST_LINES = 3
REVNO = 4
SUMMARY = 5
MESSAGE = 6
COMMITTER = 7
TIMESTAMP = 8
REVISION = 9
PARENTS = 10
CHILDREN = 11
TAGS = 12
AUTHORS = 13

class TreeModel(gtk.GenericTreeModel):

    def __init__ (self, branch, line_graph_data):
        gtk.GenericTreeModel.__init__(self)
        self.revisions = {}
        self.branch = branch
        self.repository = branch.repository
        self.line_graph_data = line_graph_data

        if self.branch.supports_tags():
            self.tags = self.branch.tags.get_reverse_tag_dict()
        else:
            self.tags = {}

    def add_tag(self, tag, revid):
        self.branch.tags.set_tag(tag, revid)
        try:
            self.tags[revid].append(tag)
        except KeyError:
            self.tags[revid] = [tag]

    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY

    def on_get_n_columns(self):
        return 14

    def on_get_column_type(self, index):
        if index == REVID: return gobject.TYPE_STRING
        if index == NODE: return gobject.TYPE_PYOBJECT
        if index == LINES: return gobject.TYPE_PYOBJECT
        if index == LAST_LINES: return gobject.TYPE_PYOBJECT
        if index == REVNO: return gobject.TYPE_STRING
        if index == SUMMARY: return gobject.TYPE_STRING
        if index == MESSAGE: return gobject.TYPE_STRING
        if index == COMMITTER: return gobject.TYPE_STRING
        if index == TIMESTAMP: return gobject.TYPE_STRING
        if index == REVISION: return gobject.TYPE_PYOBJECT
        if index == PARENTS: return gobject.TYPE_PYOBJECT
        if index == CHILDREN: return gobject.TYPE_PYOBJECT
        if index == TAGS: return gobject.TYPE_PYOBJECT
        if index == AUTHORS: return gobject.TYPE_STRING

    def on_get_iter(self, path):
        return path[0]

    def on_get_path(self, rowref):
        return rowref

    def on_get_value(self, rowref, column):
        if len(self.line_graph_data) > 0:
            (revid, node, lines, parents,
             children, revno_sequence) = self.line_graph_data[rowref]
        else:
            (revid, node, lines, parents,
             children, revno_sequence) = (None, (0, 0), (), (),
                                          (), ())
        if column == REVID: return revid
        if column == NODE: return node
        if column == LINES: return lines
        if column == PARENTS: return parents
        if column == CHILDREN: return children
        if column == LAST_LINES:
            if rowref>0:
                return self.line_graph_data[rowref-1][2]
            return []
        if column == REVNO: return ".".join(["%d" % (revno)
                                      for revno in revno_sequence])

        if column == TAGS: return self.tags.get(revid, [])

        if not revid or revid == NULL_REVISION:
            return None
        if revid not in self.revisions:
            revision = self.repository.get_revisions([revid])[0]
            self.revisions[revid] = revision
        else:
            revision = self.revisions[revid]

        if column == REVISION: return revision
        if column == SUMMARY: return escape(revision.get_summary())
        if column == MESSAGE: return escape(revision.message)
        if column == COMMITTER: return parse_username(revision.committer)[0]
        if column == TIMESTAMP:
            return strftime("%Y-%m-%d %H:%M", localtime(revision.timestamp))
        if column == AUTHORS:
            return ", ".join([
                parse_username(author)[0] for author in revision.get_apparent_authors()])

    def on_iter_next(self, rowref):
        if rowref < len(self.line_graph_data) - 1:
            return rowref+1
        return None

    def on_iter_children(self, parent):
        if parent is None: return 0
        return None

    def on_iter_has_child(self, rowref):
        return False

    def on_iter_n_children(self, rowref):
        if rowref is None: return len(self.line_graph_data)
        return 0

    def on_iter_nth_child(self, parent, n):
        if parent is None: return n
        return None

    def on_iter_parent(self, child):
        return None
