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

__copyright__ = 'Copyright (C) 2008 Daniel Schierbeck'
__author__ = 'Daniel Schierbeck <daniel.schierbeck@gmail.com>'

import dbus

BUS_NAME = 'org.gnome.seahorse'

CRYPTO_INTERFACE = 'org.gnome.seahorse.CryptoService'
CRYPTO_PATH = '/org/gnome/seahorse/crypto'

OPENPGP_INTERFACE = 'org.gnome.seahorse.Keys'
OPENPGP_PATH = '/org/gnome/seahorse/keys/openpgp'

KEY_TYPE_OPENPGP = 'openpgp'
KEY_TYPE_SSH = 'ssh'

try:
    bus = dbus.SessionBus()
    crypto = dbus.Interface(bus.get_object(BUS_NAME, CRYPTO_PATH), 
                            CRYPTO_INTERFACE)
    openpgp = dbus.Interface(bus.get_object(BUS_NAME, OPENPGP_PATH),
                             OPENPGP_INTERFACE)
except dbus.exceptions.DBusException, e:
    get_name = getattr(e, 'get_dbus_name', None)
    if get_name is not None:
        name = get_name()
    else:
        name = getattr(e, '_dbus_error_name', None)
        
    if name is None:
        args = getattr(e, 'args', None) # This is case for old python-dbus-0.62
        if args == ("Unable to determine the address of the message bus (try 'man dbus-launch' and 'man dbus-daemon' for help)",):
            raise ImportError
        
    # DBus sometimes fails like this, just treat it as if seahorse is not
    # available rather than crashing.
    if name in ("org.freedesktop.DBus.Error.Spawn.ExecFailed", 
                "org.freedesktop.DBus.Error.ServiceUnknown"):
        raise ImportError
    else:
        raise

FLAG_VALID = 0x0001
FLAG_CAN_ENCRYPT = 0x0002
FLAG_CAN_SIGN = 0x0004
FLAG_EXPIRED = 0x0100
FLAG_REVOKED = 0x0200
FLAG_DISABLED = 0x0400
FLAG_TRUSTED = 0x1000

TRUST_NEVER = -1
TRUST_UNKNOWN = 0
TRUST_MARGINAL = 1
TRUST_FULL = 5
TRUST_ULTIMATE = 10

LOCATION_MISSING = 10
LOCATION_SEARCHING = 20
LOCATION_REMOTE = 50
LOCATION_LOCAL = 100

keyset = dict()

def verify(crypttext):
    (cleartext, key) = crypto.VerifyText(KEY_TYPE_OPENPGP, 1, crypttext)

    if key != "":
        if key not in keyset:
            keyset[key] = Key(key)

        return (cleartext, keyset[key])

    return (cleartext, None)


class Key:

    def __init__(self, key):
        self.key = key

        (keys, unmatched) = openpgp.MatchKeys([self.get_id()], 0x00000010)
        self.available = (key in keys)

        if self.available:
            fields = openpgp.GetKeyFields(key, ['fingerprint', 'trust', 'flags', 'display-name', 'location'])
        else:
            fields = dict()

        self.fingerprint = fields.get('fingerprint', 'N/A')
        self.trust = fields.get('trust', TRUST_UNKNOWN)
        self.flags = fields.get('flags', 0)
        self.display_name = fields.get('display-name', '')
        self.location = fields.get('location', LOCATION_MISSING)
    
    def get_flags(self):
        return self.flags

    def get_display_name(self):
        return self.display_name

    def get_id(self):
        return self.key.split(':')[1][8:]

    def get_fingerprint(self):
        return self.fingerprint

    def get_trust(self):
        return self.trust

    def get_location(self):
        return self.location

    def is_available(self):
        return self.available

    def is_trusted(self):
        return self.flags & FLAG_TRUSTED != 0
