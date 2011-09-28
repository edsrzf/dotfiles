# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Erik Bågfors <erik@bagfors.nu>
#
# GNU GPL v2.
#
"""external merge plugin for bzr"""

try:
    from bzrlib.commands import plugin_cmds
    plugin_cmds.register_lazy('cmd_extmerge', ['emerge'],
                          'bzrlib.plugins.extmerge.extmerge')
except AttributeError:
    from bzrlib.commands import register_command
    from extmerge import cmd_extmerge
    register_command(cmd_extmerge)
