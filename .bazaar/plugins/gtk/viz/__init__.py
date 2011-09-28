# -*- coding: UTF-8 -*-
"""GTK+ Branch Visualisation.

This is a bzr plugin that adds a new 'visualise' (alias: 'viz') command
which opens a GTK+ window to allow you to see the history of the branch
and relationships between revisions in a visual manner.

It's somewhat based on a screenshot I was handed of gitk.  The top half
of the window shows the revisions in a list with a graph drawn down the
left hand side that joins them up and shows how they relate to each other.
The bottom hald of the window shows the details for the selected revision.
"""

from branchwin import BranchWindow

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"

