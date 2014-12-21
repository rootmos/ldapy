from node import Node

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

    @property
    def children (self):
        return self._cwd.relativeChildren.keys ()

    def changeDN (self, to):
        try:
            self._cwd = self._cwd.relativeChildren[to]
        except KeyError:
            raise NoSuchDN (to, self.cwd)

    def goUpOneLevel (self):
        # Test if we can go furter up
        if self._cwd.parent:
            self._cwd = self._cwd.parent
        else:
            # Otherwise we complain
            raise AlreadyAtRoot ()

    def completeChild (self, text):
        return [ i.relativeDN () for i in self._cwd.children if i.dn.startswith (text)] 
