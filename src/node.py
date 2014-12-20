import connection
import ldap
import ldap.dn

class DNError (Exception):
    def __init__ (self, dn):
        self.dn = dn

    _malformed_dn_message = "Malformed DN: %s" 

    def __str__ (self):
        return DNError._malformed_dn_message % self.dn

class NodeError (Exception):
    def __init__ (self, node, msg):
        self.node = node
        self.msg = msg

    def __str__ (self):
        return "Node(\"%s\"): %s" % (self.node.dn, self.msg)

class Node:
    """Class representing a node in the database"""

    _dn_does_not_exist = "DN does not exits: %s"

    def __init__ (self, con, dn, attributes = None):
        self.con = con
        self.dn = dn
        self.parent = None
        self._children = None
        if attributes is not None:
            self.attributes = attributes
        else:
            self._populateAttributes ()

    def _populateAttributes (self):
        try:
            nodes = self.con.ldap.search_s (self.dn, ldap.SCOPE_BASE)
            node = nodes[0]
            self.dn = node[0]
            self.attributes = node[1]
        except ldap.INVALID_DN_SYNTAX:
            raise DNError (self.dn)
        except ldap.NO_SUCH_OBJECT:
            raise NodeError (self, Node._dn_does_not_exist % self.dn)

    @property
    def children (self):
        if self._children is None:
            self._children = []
            children = self.con.ldap.search_s (self.dn, ldap.SCOPE_ONELEVEL)
            for child in children:
                node = Node (self.con, child[0], child[1])
                node.parent = self
                self._children.append (node)

        return self._children

    def relativeDN (self, to = None):
        if not to:
            to = self.parent

        toDN = ldap.dn.str2dn (str(to))
        myDN = ldap.dn.str2dn (self.dn)

        for dn in reversed (toDN):
            if dn == myDN[-1]:
                myDN.pop()
            else:
                break

        return ldap.dn.dn2str (myDN)

    def __str__ (self):
        return self.dn

