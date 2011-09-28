#!/usr/bin/python
"""GTK+ Frontends for various Bazaar commands."""

from info import *

from distutils.core import setup, Command
from distutils.command.install_data import install_data
from distutils.command.build import build
from distutils.command.sdist import sdist
import os
import sys

class Check(Command):
    description = "Run unit tests"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def get_command_name(self):
        return 'test'

    def run(self):
        from bzrlib.tests import TestLoader, TestSuite, TextTestRunner
        from bzrlib.plugin import PluginImporter
        PluginImporter.specific_paths["bzrlib.plugins.gtk"] = os.path.dirname(__file__)
        from bzrlib.plugins.gtk.tests import load_tests
        suite = TestSuite()
        loader = TestLoader()
        load_tests(suite, None, loader)
        runner = TextTestRunner()
        result = runner.run(suite)
        return result.wasSuccessful()


class CreateCredits(Command):
    description = "Create credits file"

    user_options = [("url=", None, "URL of branch")]

    def initialize_options(self):
        self.url = "."

    def finalize_options(self):
        pass

    def get_command_name(self):
        return 'build_credits'

    def run(self):
        from bzrlib.plugin import load_plugins; load_plugins()
        from bzrlib.branch import Branch
        from bzrlib.plugins.stats.cmds import find_credits

        import pickle

        branch = Branch.open(self.url)
        credits = find_credits(branch.repository, branch.last_revision())

        pickle.dump(credits, file("credits.pickle", 'w'))
        return True


def is_versioned(cmd):
    from bzrlib.errors import NotBranchError
    try:
        from bzrlib.branch import Branch
        Branch.open(".")
        return True
    except NotBranchError:
        return False


class BuildData(build):
    sub_commands = build.sub_commands[:]
    sub_commands.append(('build_credits', is_versioned))


class SourceDist(sdist):
    sub_commands = sdist.sub_commands[:]
    sub_commands.append(('build_credits', is_versioned))


class InstallData(install_data):

    def run(self):
        import subprocess
        self.data_files.extend(self._nautilus_plugin())
        install_data.run(self)

        try:
            subprocess.check_call('gtk-update-icon-cache '
                                  '-f -t /usr/share/icons/hicolor')
        except OSError:
            pass

    def _nautilus_plugin(self):
        files = []
        if sys.platform[:5] == 'linux':
            cmd = os.popen('pkg-config --variable=pythondir nautilus-python',
                           'r')
            res = cmd.readline().strip()
            ret = cmd.close()
            if ret is None:
                dest = res[5:]
                files.append((dest, ['nautilus-bzr.py']))
        return files


if __name__ == '__main__':
    version = bzr_plugin_version[:3]
    version_string = ".".join([str(x) for x in version])
    setup(
        name = "bzr-gtk",
        version = version_string,
        maintainer = "Jelmer Vernooij",
        maintainer_email = "jelmer@samba.org",
        description = "GTK+ Frontends for various Bazaar commands",
        license = "GNU GPL v2 or later",
        scripts = ['bzr-handle-patch', 'bzr-notify'],
        url = "http://bazaar-vcs.org/BzrGtk",
        package_dir = {
            "bzrlib.plugins.gtk": ".",
            "bzrlib.plugins.gtk.viz": "viz",
            "bzrlib.plugins.gtk.annotate": "annotate",
            "bzrlib.plugins.gtk.tests": "tests",
            "bzrlib.plugins.gtk.branchview": "branchview",
            "bzrlib.plugins.gtk.preferences": "preferences",
            },
        packages = [
            "bzrlib.plugins.gtk",
            "bzrlib.plugins.gtk.viz",
            "bzrlib.plugins.gtk.annotate",
            "bzrlib.plugins.gtk.tests",
            "bzrlib.plugins.gtk.branchview",
            "bzrlib.plugins.gtk.preferences",
        ],
        data_files=[ ('share/bzr-gtk', ['credits.pickle']),
                    ('share/bzr-gtk/icons', ['icons/commit.png',
                                             'icons/commit16.png',
                                             'icons/diff.png',
                                             'icons/diff16.png',
                                             'icons/log.png',
                                             'icons/log16.png',
                                             'icons/pull.png',
                                             'icons/pull16.png',
                                             'icons/push.png',
                                             'icons/push16.png',
                                             'icons/refresh.png',
                                             'icons/sign-bad.png',
                                             'icons/sign-ok.png',
                                             'icons/sign.png',
                                             'icons/sign-unknown.png',
                                             'icons/tag-16.png',
                                             'icons/bug.png',
                                             'icons/bzr-icon-64.png']),
                    ('share/applications', ['bazaar-properties.desktop',
                                            'bzr-handle-patch.desktop',
                                            'bzr-notify.desktop']),
                    ('share/application-registry', ['bzr-gtk.applications']),
                    ('share/pixmaps', ['icons/bzr-icon-64.png']),
                    ('share/icons/hicolor/scalable/apps', ['icons/bzr-panel.svg']),
                    ('share/icons/hicolor/scalable/emblems',
                     ['icons/emblem-bzr-added.svg',
                      'icons/emblem-bzr-conflict.svg',
                      'icons/emblem-bzr-controlled.svg',
                      'icons/emblem-bzr-modified.svg',
                      'icons/emblem-bzr-removed.svg',
                      'icons/emblem-bzr-ignored.svg'])
                    ],
        cmdclass={'install_data': InstallData,
                  'build_credits': CreateCredits,
                  'build': BuildData,
                  'sdist': SourceDist,
                  'check': Check}
        )
