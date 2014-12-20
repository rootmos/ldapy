from node import Node

class Ldapy:
    def __init__ (self, connection):
        self.connection = connection
        self.cwd = Node (self.connection, "")

    @property
    def cwd (self):
        return self.cwd.dn

    @property
    def attributes (self):
        return self.cwd.attributes

    @property
    def children (self):
        return self.cwd.relativeChildren.keys ()

    def changeDN (self, to):
        self.cwd = self.cwd.relativeChildren[to]
