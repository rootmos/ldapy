# This file is part of ldapy.
#
# ldapy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ldapy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ldapy.  If not, see <http://www.gnu.org/licenses/>.

class LdapError (Exception):
    def __init__ (self, exception):
        self.exception = exception

    def __str__ (self):
        return str(self.exception)

class NoSuchObject (Exception):
    def __init__ (self, dn):
        self.dn = dn
        self.matched = None

    @staticmethod
    def convert (dn, exception):
        e = NoSuchObject (dn)
        if "matched" in exception.message:
            e.matched = exception.message["matched"]
        return e

    _dn_does_not_exist = "DN does not exits: %s"

    def __str__ (self):
        return self._dn_does_not_exist % self.dn

class NoSuchObjectInRoot (Exception):
    def __init__ (self, dn):
        self.dn = dn

    _no_such_DN_in_root = "No such root DN: %s"

    def __str__ (self):
        return self._no_such_DN_in_root % self.dn

class AlreadyExists (Exception):
    def __init__ (self, dn):
        self.dn = dn

    @staticmethod
    def convert (dn, exception):
        return AlreadyExists (dn)

class DNDecodingError (Exception):
    def __init__ (self, string):
        self.string = string

    _malformed_dn_message = "Malformed DN: %s"

    def __str__ (self):
        return self._malformed_dn_message % self.string
