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

import bzrlib.errors as errors
from bzrlib.plugins.gtk import _i18n
from dialog import error_dialog, info_dialog


def show_bzr_error(unbound):
    """Decorator that shows bazaar exceptions. """
    def convert(*args, **kwargs):
        try:
            unbound(*args, **kwargs)
        except errors.NotBranchError:
            error_dialog(_i18n('Directory is not a branch'),
                         _i18n('You can perform this action only in a branch.'))
        except errors.LocalRequiresBoundBranch:
            error_dialog(_i18n('Directory is not a checkout'),
                         _i18n('You can perform local commit only on checkouts.'))
        except errors.PointlessCommit:
            error_dialog(_i18n('No changes to commit'),
                         _i18n('Try force commit if you want to commit anyway.'))
        except errors.PointlessMerge:
            info_dialog(_i18n('No changes to merge'),
                         _i18n('Merge location is already fully merged in working tree.'))
        except errors.ConflictsInTree:
            error_dialog(_i18n('Conflicts in tree'),
                         _i18n('You need to resolve the conflicts before committing.'))
        except errors.StrictCommitFailed:
            error_dialog(_i18n('Strict commit failed'),
                         _i18n('There are unknown files in the working tree.\nPlease add or delete them.'))
        except errors.BoundBranchOutOfDate, errmsg:
            error_dialog(_i18n('Bound branch is out of date'),
                         # FIXME: Really ? Internationalizing %s ?? --vila080505
                         _i18n('%s') % errmsg)
        except errors.NotVersionedError:
            error_dialog(_i18n('File not versioned'),
                         _i18n('The selected file is not versioned.'))
        except errors.DivergedBranches:
            error_dialog(_i18n('Branches have been diverged'),
                         _i18n('You cannot push if branches have diverged. Use the\noverwrite option if you want to push anyway.'))
        except errors.NoSuchFile:
            error_dialog(_i18n("No diff output"),
                         _i18n("The selected file hasn't changed."))
        except errors.NoSuchRevision:
                error_dialog(_i18n('No such revision'),
                             _i18n("The revision you specified doesn't exist."))
        except errors.FileExists:
                error_dialog(_i18n('Target already exists'),
                             _i18n("Target directory already exists. Please select another target."))
        except errors.AlreadyBranchError, errmsg:
            error_dialog(_i18n('Directory is already a branch'),
                         _i18n('The current directory (%s) is already a branch.\nYou can start using it, or initialize another directory.') % errmsg)
        except errors.BranchExistsWithoutWorkingTree, errmsg:
            error_dialog(_i18n('Branch without a working tree'),
                         _i18n('The current directory (%s)\nis a branch without a working tree.') % errmsg)
        except errors.BzrError, msg:
            error_dialog(_i18n('Unknown bzr error'), str(msg))
        except errors.PermissionDenied:
            error_dialog(_i18n("Permission denied"), _i18n("permission denied."))
        except Exception, msg:
            error_dialog(_i18n('Unknown error'), str(msg))

    convert.__doc__ = unbound.__doc__
    convert.__name__ = unbound.__name__
    return convert



