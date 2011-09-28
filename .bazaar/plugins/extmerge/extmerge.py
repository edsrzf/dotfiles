# -*- coding: utf-8 -*-
# Copyright (C) 2006 Erik Bågfors <erik@bagfors.nu>
#
# GNU GPL v2.
#


import errno
import exceptions
import os
import shutil
from subprocess import call
import tempfile

from bzrlib.commands import Command, register_command
from bzrlib.config import GlobalConfig
from bzrlib.conflicts import CONFLICT_SUFFIXES
from bzrlib.errors import BzrCommandError
from bzrlib.option import Option
from bzrlib.workingtree import WorkingTree


# The same syntax as in mergetools below, can be used in external_merge
# in bazaar.conf
# %b = base  (foo.BASE)
# %t = this  (foo.THIS)
# %o = other (foo.OTHER)
# %r = resolved file (aka output file) (foo)
# %T = this  (foo.THIS), a temporary copy of foo.THIS; will be used to
#                        overwrite 'foo' if the merge succeeds

valid_parameter_sets = (
    # normal 3 way merge + output file
    ('%r', '%b', '%t', '%o'),
    # meld-style 3 way merge, one file (%T) being used for both in- and output
    ('%b', '%T', '%o'),
    # meld-style 2 way merge, one file (%T) being used for both in- and output
    ('%T', '%o')
)

mergetools = [
    'bcompare %t %o %b %r',
    'kdiff3 --output %r %b %t %o',
    'xxdiff -m -O -M %r %t %b %o',
    'meld %b %T %o',
    'opendiff %t %o -ancestor %b -merge %r'
]


class cmd_extmerge(Command):
    """Calls an external merge program such as meld, xxdiff, kdiff3, opendiff,
    Beyond Compare, etc to help you resolve any conflicts you have.

    Will call a user defined merge tool if it exists, otherwise, will try
    bcompare, kdiff3, xxdiff, meld and opendiff, in that order.

    To define your own merge tool, set external_merge in bazaar.conf.
    See extmerge/extmerge.py for the syntax.
    """
    aliases = ['emerge']
    takes_args = ['file*']
    takes_options = [Option('all', help='Use all files with conflicts.')]

    def run(self, file_list, all=False):
        if file_list is None:
            if not all:
                raise BzrCommandError(
                    "command 'extmerge' needs one or more FILE, or --all")
            tree = WorkingTree.open_containing(u'.')[0]
            file_list = list(tree.abspath(f.path) for f in tree.conflicts())
        else:
            if all:
                raise BzrCommandError(
                        "If --all is specified, no FILE may be provided")
        for filename in file_list:
            if not os.path.exists(filename):
                print "%s does not exists" % filename
            else:
                failures = 0
                for suffix in CONFLICT_SUFFIXES:
                    if not os.path.exists(filename + suffix) and not failures:
                        print "%s is not conflicted" % filename
                        failures = 1
                    
                if not failures:
                    run_extmerge(filename)
        if len(file_list) == 0:
            print "no conflicting files"
        else:
            # TODO: ask if the file(s) should get resolved, per file.
            print "remember to bzr resolve your files"


def get_user_merge_tool():
    return GlobalConfig().get_user_option('external_merge')


def validate_command(tool):
    """Validates that 'tool' contains at least one set of 'valid_parameter_sets'"""

    def check_substrings(string, substrings):
        """Checks if all 'substrings' occur in 'string'"""
        for e in substrings:
            if not e in string:
                return False

        return True

    sets = map(lambda x: check_substrings(tool, x), valid_parameter_sets)

    # not a single valid-parameter-set present -> BzrCommandError
    if not True in sets:
        raise BzrCommandError(
            "Error in external merge tool definition.\n" +
            "Definition needs to contain one of the following parameter sets:\n" +
            "".join(map(
                lambda x:
                    "\t- %s\n" % x,
                    map(", ".join, valid_parameter_sets)
            )) +
            "Definition is %s" % tool
        )


def execute_command(tool, filename):
    tool = tool.replace('%r', filename)
    tool = tool.replace('%t', filename + '.THIS')
    tool = tool.replace('%o', filename + '.OTHER')
    tool = tool.replace('%b', filename + '.BASE')

    # create tmpfile for %T (if needed)
    this_tmp = False
    if '%T' in tool:
        this_tmp = tempfile.mktemp("_bzr_extmerge_%s.THIS" % os.path.basename(filename))
        shutil.copy(filename + ".THIS", this_tmp)
        tool = tool.replace('%T', this_tmp)

    ret = call(tool.split(' '))

    # cleanup tmpfile of %T
    if this_tmp:
        # merge success -> keep changes
        if ret == 0:
            shutil.move(this_tmp, filename)
        # merge failed -> delete file
        else:
            os.remove(this_tmp)

    return ret

OK_ERRNO = (errno.ENOENT, errno.EACCES)

def run_extmerge(filename):
    global mergetools
    usertool = get_user_merge_tool()
    if usertool:
        mergetools = [usertool]

    for tool in mergetools:
        validate_command(tool)
        try:
            ret = execute_command(tool, filename)
        except OSError, e:
            # ENOENT means no such editor
            if e.errno in OK_ERRNO:
                continue
            raise
        if ret == 0:
            return True
        elif ret == 127:
            continue
        else:
            mergetools = [tool]
            break

    if len(mergetools) != 1:
        raise BzrCommandError("Found no valid merge tool")
