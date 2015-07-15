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

from node import Node, NodeError
import argparse
import ldapurl
import connection
import exceptions
import sys

import logging
logger = logging.getLogger("ldapy.%s" % __name__)


class LdapyError (Exception):
    def __str__ (self):
        return self.msg

class AlreadyAtRoot (LdapyError):
    def __init__ (self):
        self.msg = self._already_at_root

    _already_at_root = "Already at root."

class SetAttributeError (LdapyError):
    def __init__ (self, msg):
        self.msg = msg

class DeleteError (LdapyError):
    def __init__ (self, msg):
        self.msg = msg

class Ldapy:
    def __init__ (self, con = None):
        if con:
            self.connection = con
        else:
            self.parseArguments ()

            try:
                self.connection = connection.Connection (self.args.URI)
                self.connection.bind (self.args.bind_dn, self.args.password)
            except connection.ConnectionError as e:
                logger.critical (e)
                sys.exit (1)

        self._cwd = Node (self.connection, "")

    @property
    def cwd (self):
        return self._cwd.dn

    @property
    def attributes (self):
        return self._cwd.attributes

    def _resolveRelativeDN (self, relDN):
        if relDN == ".":
            return self._cwd
        elif relDN == "..":
            if self._cwd.parent:
                return self._cwd.parent
            else:
                raise AlreadyAtRoot ()
        else:
            try:
                return self._cwd.relativeChildren[relDN]
            except KeyError:
                if self.cwd:
                    raise exceptions.NoSuchObject ("%s,%s" % (relDN, self.cwd))
                else:
                    raise exceptions.NoSuchObjectInRoot (relDN)

    def getAttributes (self, relDN):
        return self._resolveRelativeDN (relDN).attributes

    def setAttribute (self, relDN, attribute, newValue = None, oldValue = None):
        try:
            return self._resolveRelativeDN (relDN).setAttribute (attribute,
                    newValue = newValue, oldValue = oldValue)
        except NodeError as e:
            raise SetAttributeError (e.msg)

    def delete (self, relDN):
        try:
            self._resolveRelativeDN (relDN).delete ()
        except NodeError as e:
            raise DeleteError (e.msg)

    @property
    def children (self):
        return self._cwd.relativeChildren.keys ()

    def changeDN (self, to):
        self._cwd = self._resolveRelativeDN (to)

    def goUpOneLevel (self):
        self.changeDN ("..")

    def completeChild (self, text):
        return [ i.relativeDN () for i in self._cwd.children if i.dn.startswith (text)]


    _neither_host_nor_uri_given = "Must specify either a host (--host) or an URI."
    _both_host_and_uri_given = "Both host and URI specified, only one allowed."
    _uri_malformed = "Invalid URI format given."
    _port_is_not_a_valid_number = "Port is not a valid number."

    def parseArguments (self, args = None, name = "ldapy"):
        parser = argparse.ArgumentParser (prog=name)

        parser.add_argument ("--host", "-H",
                             help="Specifies host to connect to.")
        parser.add_argument ("--port", "-p", default=389, type=int,
                             help="Specifies which port to connect to on host.")
        parser.add_argument ("--bind-dn", "-D", default="",
                             help="Specifies DN used for binding.")
        parser.add_argument ("--password", "-w", default="",
                             help="Specifies password used for binding.")
        parser.add_argument ("URI", nargs="?",
                help="Specifies URI to connect to, in the format: ldap://host[:port]")
        parser.add_argument ("--verbose", "-v", default=False, action="store_true",
                help="Output more information about what's happening behind the scenes.")
        parser.add_argument ("--debug", "-d", default=False, action="store_true",
                help="Output all available gruesome debug information.")
        self.args = parser.parse_args (args)

        # Take this opportunity to set the logging levels as early as possible
        self.setLoggingLevels ()

        return self.validateArguments (parser)

    def validateArguments (self, parser):
        if not self.args.host and not self.args.URI:
            parser.error (Ldapy._neither_host_nor_uri_given)
            return False

        if self.args.host and self.args.URI:
            parser.error (Ldapy._both_host_and_uri_given)
            return False

        if self.args.URI:
            try:
                uri = ldapurl.LDAPUrl (self.args.URI)
                hostport = uri.hostport.split (":")
                self.args.host = hostport[0]
                if len(hostport) == 2:
                    self.args.port = int(hostport[1])
            except ValueError:
                parser.error (Ldapy._uri_malformed)
                return False
        else:
            self.args.URI = "ldap://%s:%s" % (self.args.host, self.args.port)

        if self.args.port < 0 or self.args.port > 0xffff:
            parser.error (Ldapy._port_is_not_a_valid_number)
            return False

        logger.debug ("Arguments: %s" % vars(self.args))

        return True

    def setLoggingLevels (self):
        # Obtain the global ldapy logger
        logger = logging.getLogger("ldapy")

        if self.args.debug:
            logger.setLevel (logging.DEBUG)
        elif self.args.verbose:
            logger.setLevel (logging.INFO)
