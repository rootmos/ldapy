from node import Node
import argparse
import logging
import ldapurl

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
    def __init__ (self, connection):
        self.connection = connection
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
    _both_host_and_uri_given_and_unequal = "Ambiguous host and URI specified."
    _uri_malformed = "Invalid URI format given."

    def parseArguments (self, args):
        parser = argparse.ArgumentParser ()

        parser.add_argument ("--host", "-H",
                             help="Specifies host to connect to.")
        parser.add_argument ("--port", "-p",
                             help="Specifies which port to connect to on host.")
        parser.add_argument ("URI", nargs="*", default=None,
                help="Specifies URI to connect to, in the format: ldap://host[:port]")
        parser.add_argument ("--bind-dn", "-D",
                             help="Specifies DN used for binding.")
        parser.add_argument ("--password", "-w",
                             help="Specifies password used for binding.")

        self.args = parser.parse_args (args)
        return self.validateArguments ()

    def validateArguments (self):
        if not self.args.host and not self.args.URI:
            logging.error (Ldapy._neither_host_nor_uri_given)
            return False

        if self.args.URI and len(self.args.URI) == 1:
            try:
                uri = ldapurl.LDAPUrl (self.args.URI[0])
            except ValueError:
                logging.error (Ldapy._uri_malformed)
                return False

        return True

