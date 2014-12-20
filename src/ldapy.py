from node import Node

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
        self._cwd = self._cwd.relativeChildren[to]
