import connection
import ldap

class DNError (Exception):
    def __init__ (self, dn):
        self.dn = dn

    def __str__ (self):
        return "Malformed DN: %s" % self.dn

class NodeError (Exception):
    def __init__ (self, node, msg):
        self.node = node
        self.msg = msg

    def __str__ (self):
        return "Node(\"%s\"): %s" % (self.node.dn, self.msg)

class Node:
    """Class representing a node in the database"""

    _dn_does_not_exist = "DN does not exits: %s"

    def __init__ (self, con, dn):
        self.con = con
        self.dn = dn
        try:
            con.ldap.search_s (dn, ldap.SCOPE_BASE)
        except ldap.INVALID_DN_SYNTAX:
            raise DNError (dn)
        except ldap.NO_SUCH_OBJECT:
            raise NodeError (self, Node._dn_does_not_exist % dn)
