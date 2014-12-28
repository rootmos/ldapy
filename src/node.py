import connection
import ldap
import ldap.dn
import logging

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
    _attributes_failed = "Unable to obtain attributes for: %s"

    def __init__ (self, con, dn, attributes = None):
        logging.info ("Creating Node with DN=[%s]" % dn)
        self.con = con
        self.dn = dn
        self.parent = None
        self._children = None
        self._relativeChildren = None

        # If we were'n given a dn, then we populate the Node with the roots
        if not self.dn:
            logging.debug ("Populating root node with roots: %s" % self.con.roots)
            self._children = []
            for root in self.con.roots:
                try:
                    node = Node (self.con, root)
                    node.parent = self
                    self._children.append (node)
                except NodeError as e:
                    logging.error (e)
                    logging.error ("Skipping root %s" % root)

        # If we were given our attributes, thank the caller, otherwise we
        # populate them ourselves
        if attributes is not None:
            self.attributes = attributes
        else:
            self._populateAttributes ()

    def _populateAttributes (self):
        # If we are the root node, then we don't have any attributes
        if not self.dn:
            self.attributes = {}
            return

        try:
            logging.debug ("Getting attributes for DN=[%s]" % self.dn)
            nodes = self.con.ldap.search_s (self.dn, ldap.SCOPE_BASE)
            node = nodes[0]
            self.dn = node[0]
            self.attributes = node[1]
            logging.debug ("Attributes: %s" % self.attributes)
        except ldap.INVALID_DN_SYNTAX:
            raise DNError (self.dn)
        except ldap.NO_SUCH_OBJECT:
            raise NodeError (self, Node._dn_does_not_exist % self.dn)
        except ldap.OTHER:
            raise NodeError (self, Node._attributes_failed % self.dn)

    @property
    def children (self):
        if self._children is None:
            self._children = []
            children = self.con.ldap.search_s (self.dn, ldap.SCOPE_ONELEVEL)
            for child in children:
                node = Node (self.con, child[0], child[1])
                node.parent = self
                self._children.append (node)

            logging.debug ("Populated DN=[%s] with children: %s" % (self.dn, self._children))

        return self._children

    @property
    def relativeChildren (self):
        if self._relativeChildren is None:
            self._relativeChildren = {}
            for child in self.children:
                self._relativeChildren[child.relativeDN()] = child

        return self._relativeChildren


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

