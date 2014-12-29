from node import Node
import argparse
import ldapurl
import connection
import sys

import logging
logger = logging.getLogger("ldapy").getChild(__name__)

class NoSuchDN (Exception):
    def __init__ (self, relDN, parent):
        self.relDN = relDN
        self.parent = parent

    _no_such_DN_in_root = "No such root DN: %s"
    _no_such_DN_in_parent = "No such DN: %s,%s"

    def __str__ (self):
        if self.parent:
            return NoSuchDN._no_such_DN_in_parent % (self.relDN, self.parent)
        else:
            return NoSuchDN._no_such_DN_in_root % (self.relDN)

class AlreadyAtRoot (Exception):
    _already_at_root = "Already at root."

    def __str__ (self):
        return AlreadyAtRoot._already_at_root


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
                raise NoSuchDN (relDN, self.cwd)

    def getAttributes (self, relDN):
        return self._resolveRelativeDN (relDN).attributes

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

        self.args = parser.parse_args (args)
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

