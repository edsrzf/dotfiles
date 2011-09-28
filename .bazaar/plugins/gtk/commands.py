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

import os

from bzrlib import (
    branch,
    errors,
    workingtree,
    )
from bzrlib.commands import (
    Command,
    display_command,
    )
from bzrlib.errors import (
    BzrCommandError,
    NoWorkingTree,
    NotVersionedError,
    NoSuchFile,
    )
from bzrlib.option import Option

from bzrlib.plugins.gtk import (
    _i18n,
    import_pygtk,
    set_ui_factory,
    )


class NoDisplayError(errors.BzrCommandError):
    """gtk could not find a proper display"""

    def __str__(self):
        return "No DISPLAY. Unable to run GTK+ application."


def open_display():
    pygtk = import_pygtk()
    try:
        import gtk
    except RuntimeError, e:
        if str(e) == "could not open display":
            raise NoDisplayError
    set_ui_factory()
    return gtk



class GTKCommand(Command):
    """Abstract class providing GTK specific run commands."""

    def run(self):
        open_display()
        dialog = self.get_gtk_dialog(os.path.abspath('.'))
        dialog.run()


class cmd_gbranch(GTKCommand):
    """GTK+ branching.
    
    """

    def get_gtk_dialog(self, path):
        from bzrlib.plugins.gtk.branch import BranchDialog
        return BranchDialog(path)


class cmd_gcheckout(GTKCommand):
    """ GTK+ checkout.
    
    """
    
    def get_gtk_dialog(self, path):
        from bzrlib.plugins.gtk.checkout import CheckoutDialog
        return CheckoutDialog(path)



class cmd_gpush(GTKCommand):
    """ GTK+ push.
    
    """
    takes_args = [ "location?" ]

    def run(self, location="."):
        (br, path) = branch.Branch.open_containing(location)
        open_display()
        from bzrlib.plugins.gtk.push import PushDialog
        dialog = PushDialog(br.repository, br.last_revision(), br)
        dialog.run()


class cmd_gloom(GTKCommand):
    """ GTK+ loom.
    
    """
    takes_args = [ "location?" ]

    def run(self, location="."):
        try:
            (tree, path) = workingtree.WorkingTree.open_containing(location)
            br = tree.branch
        except NoWorkingTree, e:
            (br, path) = branch.Branch.open_containing(location)
            tree = None
        open_display()
        from bzrlib.plugins.gtk.loom import LoomDialog
        dialog = LoomDialog(br, tree)
        dialog.run()


class cmd_gdiff(GTKCommand):
    """Show differences in working tree in a GTK+ Window.
    
    Otherwise, all changes for the tree are listed.
    """
    takes_args = ['filename?']
    takes_options = ['revision']

    @display_command
    def run(self, revision=None, filename=None):
        set_ui_factory()
        wt = workingtree.WorkingTree.open_containing(".")[0]
        wt.lock_read()
        try:
            branch = wt.branch
            if revision is not None:
                if len(revision) == 1:
                    tree1 = wt
                    revision_id = revision[0].as_revision_id(tree1.branch)
                    tree2 = branch.repository.revision_tree(revision_id)
                elif len(revision) == 2:
                    revision_id_0 = revision[0].as_revision_id(branch)
                    tree2 = branch.repository.revision_tree(revision_id_0)
                    revision_id_1 = revision[1].as_revision_id(branch)
                    tree1 = branch.repository.revision_tree(revision_id_1)
            else:
                tree1 = wt
                tree2 = tree1.basis_tree()

            from diff import DiffWindow
            import gtk
            window = DiffWindow()
            window.connect("destroy", gtk.main_quit)
            window.set_diff("Working Tree", tree1, tree2)
            if filename is not None:
                tree_filename = wt.relpath(filename)
                try:
                    window.set_file(tree_filename)
                except NoSuchFile:
                    if (tree1.path2id(tree_filename) is None and 
                        tree2.path2id(tree_filename) is None):
                        raise NotVersionedError(filename)
                    raise BzrCommandError('No changes found for file "%s"' % 
                                          filename)
            window.show()

            gtk.main()
        finally:
            wt.unlock()


def start_viz_window(branch, revisions, limit=None):
    """Start viz on branch with revision revision.
    
    :return: The viz window object.
    """
    from bzrlib.plugins.gtk.viz import BranchWindow
    return BranchWindow(branch, revisions, limit)


class cmd_visualise(Command):
    """Graphically visualise one or several branches.

    Opens a graphical window to allow you to see branches history and
    relationships between revisions in a visual manner,

    If no revision is specified, the branch last revision is taken as a
    starting point. When a revision is specified, the presented graph starts
    with it (as a side effect, when a shared repository is used, any revision
    can be used even if it's not part of the branch history).
    """
    takes_options = [
        "revision",
        Option('limit', "Maximum number of revisions to display.",
               int, 'count')]
    takes_args = [ "locations*" ]
    aliases = [ "visualize", "vis", "viz" ]

    def run(self, locations_list, revision=None, limit=None):
        set_ui_factory()
        if locations_list is None:
            locations_list = ["."]
        revids = []
        for location in locations_list:
            (br, path) = branch.Branch.open_containing(location)
            if revision is None:
                revids.append(br.last_revision())
            else:
                revids.append(revision[0].as_revision_id(br))
        import gtk
        pp = start_viz_window(br, revids, limit)
        pp.connect("destroy", lambda w: gtk.main_quit())
        pp.show()
        gtk.main()


class cmd_gannotate(GTKCommand):
    """GTK+ annotate.
    
    Browse changes to FILENAME line by line in a GTK+ window.

    Within the annotate window, you can use Ctrl-F to search for text, and 
    Ctrl-G to jump to a line by number.
    """

    takes_args = ["filename", "line?"]
    takes_options = [
        Option("all", help="Show annotations on all lines."),
        Option("plain", help="Don't highlight annotation lines."),
        Option("line", type=int, argname="lineno",
               help="Jump to specified line number."),
        "revision",
    ]
    aliases = ["gblame", "gpraise"]
    
    def run(self, filename, all=False, plain=False, line='1', revision=None):
        gtk = open_display()

        try:
            line = int(line)
        except ValueError:
            raise BzrCommandError('Line argument ("%s") is not a number.' % 
                                  line)

        from annotate.gannotate import GAnnotateWindow
        from annotate.config import GAnnotateConfig
        from bzrlib.bzrdir import BzrDir

        wt, br, path = BzrDir.open_containing_tree_or_branch(filename)
        if wt is not None:
            tree = wt
        else:
            tree = br.basis_tree()

        file_id = tree.path2id(path)

        if file_id is None:
            raise NotVersionedError(filename)
        if revision is not None:
            if len(revision) != 1:
                raise BzrCommandError("Only 1 revion may be specified.")
            revision_id = revision[0].as_revision_id(br)
            tree = br.repository.revision_tree(revision_id)
        else:
            revision_id = getattr(tree, 'get_revision_id', lambda: None)()

        window = GAnnotateWindow(all, plain, branch=br)
        window.connect("destroy", lambda w: gtk.main_quit())
        config = GAnnotateConfig(window)
        window.show()
        br.lock_read()
        if wt is not None:
            wt.lock_read()
        try:
            window.annotate(tree, br, file_id)
            window.jump_to_line(line)
            gtk.main()
        finally:
            br.unlock()
            if wt is not None:
                wt.unlock()



class cmd_gcommit(GTKCommand):
    """GTK+ commit dialog

    Graphical user interface for committing revisions"""

    aliases = [ "gci" ]
    takes_args = []
    takes_options = []

    def run(self, filename=None):
        open_display()
        from commit import CommitDialog

        wt = None
        br = None
        try:
            (wt, path) = workingtree.WorkingTree.open_containing(filename)
            br = wt.branch
        except NoWorkingTree, e:
            from dialog import error_dialog
            error_dialog(_i18n('Directory does not have a working tree'),
                         _i18n('Operation aborted.'))
            return 1 # should this be retval=3?

        # It is a good habit to keep things locked for the duration, but it
        # could cause difficulties if someone wants to do things in another
        # window... We could lock_read() until we actually go to commit
        # changes... Just a thought.
        wt.lock_write()
        try:
            dlg = CommitDialog(wt)
            return dlg.run()
        finally:
            wt.unlock()


class cmd_gstatus(GTKCommand):
    """GTK+ status dialog

    Graphical user interface for showing status 
    information."""

    aliases = [ "gst" ]
    takes_args = ['PATH?']
    takes_options = ['revision']

    def run(self, path='.', revision=None):
        gtk = open_display()
        from bzrlib.plugins.gtk.status import StatusWindow
        (wt, wt_path) = workingtree.WorkingTree.open_containing(path)

        if revision is not None:
            try:
                revision_id = revision[0].as_revision_id(wt.branch)
            except:
                from bzrlib.errors import BzrError
                raise BzrError('Revision %r doesn\'t exist'
                               % revision[0].user_spec )
        else:
            revision_id = None

        status = StatusWindow(wt, wt_path, revision_id)
        status.connect("destroy", gtk.main_quit)
        status.show()
        gtk.main()


class cmd_gsend(GTKCommand):
    """GTK+ send merge directive.

    """
    def run(self):
        (br, path) = branch.Branch.open_containing(".")
        gtk = open_display()
        from bzrlib.plugins.gtk.mergedirective import SendMergeDirectiveDialog
        from StringIO import StringIO
        dialog = SendMergeDirectiveDialog(br)
        if dialog.run() == gtk.RESPONSE_OK:
            outf = StringIO()
            outf.writelines(dialog.get_merge_directive().to_lines())
            mail_client = br.get_config().get_mail_client()
            mail_client.compose_merge_request(dialog.get_mail_to(), "[MERGE]", 
                outf.getvalue())

            


class cmd_gconflicts(GTKCommand):
    """GTK+ conflicts.
    
    Select files from the list of conflicts and run an external utility to
    resolve them.
    """
    def run(self):
        (wt, path) = workingtree.WorkingTree.open_containing('.')
        open_display()
        from bzrlib.plugins.gtk.conflicts import ConflictsDialog
        dialog = ConflictsDialog(wt)
        dialog.run()


class cmd_gpreferences(GTKCommand):
    """ GTK+ preferences dialog.

    """
    def run(self):
        open_display()
        from bzrlib.plugins.gtk.preferences import PreferencesWindow
        dialog = PreferencesWindow()
        dialog.run()


class cmd_gmerge(Command):
    """ GTK+ merge dialog
    
    """
    takes_args = ["merge_from_path?"]
    def run(self, merge_from_path=None):
        from bzrlib.plugins.gtk.dialog import error_dialog
        from bzrlib.plugins.gtk.merge import MergeDialog
        
        (wt, path) = workingtree.WorkingTree.open_containing('.')
        old_tree = wt.branch.repository.revision_tree(wt.branch.last_revision())
        delta = wt.changes_from(old_tree)
        if len(delta.added) or len(delta.removed) or len(delta.renamed) or len(delta.modified):
            error_dialog(_i18n('There are local changes in the branch'),
                         _i18n('Please commit or revert the changes before merging.'))
        else:
            parent_branch_path = wt.branch.get_parent()
            merge = MergeDialog(wt, path, parent_branch_path)
            response = merge.run()
            merge.destroy()


class cmd_gmissing(Command):
    """ GTK+ missing revisions dialog.

    """
    takes_args = ["other_branch?"]
    def run(self, other_branch=None):
        pygtk = import_pygtk()
        try:
            import gtk
        except RuntimeError, e:
            if str(e) == "could not open display":
                raise NoDisplayError

        from bzrlib.plugins.gtk.missing import MissingWindow
        from bzrlib.branch import Branch

        local_branch = Branch.open_containing(".")[0]
        if other_branch is None:
            other_branch = local_branch.get_parent()
            
            if other_branch is None:
                raise BzrCommandError("No peer location known or specified.")
        remote_branch = Branch.open_containing(other_branch)[0]
        set_ui_factory()
        local_branch.lock_read()
        try:
            remote_branch.lock_read()
            try:
                dialog = MissingWindow(local_branch, remote_branch)
                dialog.run()
            finally:
                remote_branch.unlock()
        finally:
            local_branch.unlock()


class cmd_ginit(GTKCommand):
    """ GTK+ init dialog

    Graphical user interface for initializing new branches.

    """
    def run(self):
        open_display()
        from initialize import InitDialog
        dialog = InitDialog(os.path.abspath(os.path.curdir))
        dialog.run()


class cmd_gtags(GTKCommand):
    """ GTK+ tags dialog 

    Graphical user interface to view, create, or remove tags.

    """
    def run(self):
        br = branch.Branch.open_containing('.')[0]
        
        gtk = open_display()
        from tags import TagsWindow
        window = TagsWindow(br)
        window.show()
        gtk.main()
