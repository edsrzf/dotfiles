# Copyright (C) 2007 Jelmer Vernooij <jelmer@samba.org>
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

delimiter = " "

class UrlHistory:
    """Simple helper class for storing URL history."""

    def __init__(self, config, name):
        """Access URL History in a Config object.

        :param config: Config object to use
        :param name: Name of the history variable.
        """
        self._config = config
        self._name = name

    def add_entry(self, url):
        """Add a new entry to the list.

        :param url: Url to add
        """
        self._config.set_user_option(self._name, delimiter.join(
            self.get_entries() + [url]))

    def get_entries(self):
        """Obtain all URLs currently listed.

        :return list of URLs or empty list if no URLs set yet.
        """
        history = self._config.get_user_option(self._name)
        if history is None:
            return []
        else:
            return history.split(delimiter)
