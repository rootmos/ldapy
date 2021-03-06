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

import ldap
import ldap.modlist
import sys
import exceptions

import logging
logger = logging.getLogger("ldapy.%s" %  __name__)

import ldap.dn

class ConnectionError (Exception):
    def __init__ (self, con, msg, info = None):
        self.con = con
        self.msg = msg
        self.info = info

    def __str__ (self):
        if self.info:
            return self.msg + " Info: " + self.info
        else:
            return self.msg

def dn2str (dn):
    return ldap.dn.dn2str (dn)

def str2dn (string):
    try:
        return ldap.dn.str2dn (string)
    except ldap.DECODING_ERROR:
        raise exceptions.DNDecodingError(string)

class Connection:
    """The class managing the LDAP connection."""

    _connection_error_msg = "Unable to connect to %s."
    _bad_auth_error_msg = "Unable to authenticate user: %s."
    _server_unwilling = "Server unwilling to perform requested operation."

    def __init__ (self, uri, traces = 0):
        logger.info ("Connecting to %s" % uri)
        self.uri = uri
        self._ldap = ldap.initialize (uri, trace_level = traces, trace_file = sys.stdout)
        self.connected = False
        self._roots = None

    def _raise_error (self, msg, exception = None):
        if exception and hasattr(exception, "message") and exception.message.has_key ("info"):
            raise ConnectionError (self, msg, exception.message["info"])
        else:
            raise ConnectionError (self, msg)


    def bind (self, who, cred):
        try:
            self._ldap.simple_bind_s (who, cred)
        except ldap.SERVER_DOWN as e:
            self._raise_error (Connection._connection_error_msg % self.uri, e)
        except ldap.INVALID_CREDENTIALS as e:
            self._raise_error (Connection._bad_auth_error_msg % who, e)
        except ldap.UNWILLING_TO_PERFORM as e:
            self._raise_error (Connection._server_unwilling, e)

        self.connected = True

    @property
    def roots (self):
        if not self._roots:
            results = self._ldap.search_s ("", ldap.SCOPE_BASE, attrlist = ["namingContexts"])
            self._roots = results[0][1]["namingContexts"]

            logger.debug ("Roots: %s" % self._roots)

        return self._roots


    def search (self, dn, scope, attrlist = None):
        try:
            return self._ldap.search_s (dn, scope, attrlist = attrlist)
        except ldap.NO_SUCH_OBJECT as e:
            raise exceptions.NoSuchObject.convert(dn, e)
        except ldap.LDAPError as e:
            raise exceptions.LdapError (e)

    def modify (self, dn, oldAttrs, newAttrs):
        try:
            ldif = ldap.modlist.modifyModlist (oldAttrs, newAttrs)
            logger.debug ("LdapModify: dn=%s, ldif:\n%s" % (dn, ldif))
            self._ldap.modify_s (dn, ldif)
        except ldap.UNDEFINED_TYPE as e:
            raise exceptions.UndefinedType.convert (e)
        except ldap.TYPE_OR_VALUE_EXISTS as e:
            raise exceptions.TypeOrValueExists.convert (e, dn, newAttrs)
        except ldap.LDAPError as e:
            raise exceptions.LdapError (e)

    def delete (self, dn):
        try:
            self._ldap.delete_s (dn)
        except ldap.NO_SUCH_OBJECT as e:
            raise exceptions.NoSuchObject.convert (dn, e)
        except ldap.LDAPError as e:
            raise exceptions.LdapError (e)

    def add (self, dn, attrs):
        ldif = ldap.modlist.addModlist (attrs)
        try:
            self._ldap.add_s (dn, ldif)
        except ldap.NO_SUCH_OBJECT as e:
            raise exceptions.NoSuchObject.convert (dn, e)
        except ldap.ALREADY_EXISTS as e:
            raise exceptions.AlreadyExists.convert (dn, e)
        except ldap.UNDEFINED_TYPE as e:
            raise exceptions.UndefinedType.convert (e)
        except ldap.TYPE_OR_VALUE_EXISTS as e:
            raise exceptions.TypeOrValueExists.convert (e, dn, attrs)
        except ldap.LDAPError as e:
            raise exceptions.LdapError (e)


scopeOneLevel = ldap.SCOPE_ONELEVEL
scopeBase = ldap.SCOPE_BASE
