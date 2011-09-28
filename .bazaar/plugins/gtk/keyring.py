# Copyright (C) 2009 Jelmer Vernooij <jelmer@samba.org>

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

import gobject
try:
    import gnomekeyring
except ImportError:
    gnomekeyring = None

from bzrlib.config import (
    CredentialStore,
    )


class GnomeKeyringCredentialStore(CredentialStore):

    def __init__(self):
        CredentialStore.__init__(self)
        # Older versions of gobject don't provide get_application_name so we
        # can't always check.
        get_app_name = getattr(gobject, 'get_application_name', None)
        if get_app_name is None or get_app_name() is None:
            # External applications that load bzrlib may already have set the
            # application name so we don't contradict them (when we can
            # determine it that is).
            gobject.set_application_name("bzr")

    def decode_password(self, credentials):
        if gnomekeyring is None:
            return None
        attrs = {}
        if "scheme" in credentials:
            attrs["protocol"] = credentials["scheme"].encode("utf-8")
        if "host" in credentials:
            attrs["server"] = credentials["host"].encode("utf-8")
        if "user" in credentials:
            attrs["user"] = credentials["user"].encode("utf-8")
        if credentials.get("port") is not None:
            attrs["port"] = credentials["port"]
        try:
            items = gnomekeyring.find_items_sync(
                gnomekeyring.ITEM_NETWORK_PASSWORD, attrs)
            return items[0].secret
        except (gnomekeyring.NoMatchError, gnomekeyring.DeniedError):
            return None

    def get_credentials(self, scheme, host, port=None, user=None, path=None, 
                        realm=None):
        if gnomekeyring is None:
            return None
        attrs = {
            "protocol": scheme.encode("utf-8"),
            "server": host.encode("utf-8"),
            }
        # TODO: realm ?
        if port is not None:
            attrs["port"] = port
        if user is not None:
            attrs["user"] = user.encode("utf-8")
        credentials = { "scheme": scheme, "host": host, "port": port, 
            "realm": realm, "user": user}
        try:
            items = gnomekeyring.find_items_sync(
                gnomekeyring.ITEM_NETWORK_PASSWORD, attrs)
            credentials["user"] = items[0].attributes["user"]
            credentials["password"] = items[0].secret
            return credentials
        except (gnomekeyring.NoMatchError, gnomekeyring.DeniedError, gnomekeyring.NoKeyringDaemonError,
                gnomekeyring.IOError), e:
            from bzrlib import trace
            trace.mutter('Unable to obtain credentials for %r from GNOME keyring: %r',
                         attrs, e)
            return None
