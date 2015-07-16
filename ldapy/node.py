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

import connection
import exceptions

import logging
logger = logging.getLogger("ldapy.%s" % __name__)

class NodeError (Exception):
    def __init__ (self, node, msg):
        self.node = node
        self.msg = msg

    def __str__ (self):
        return "Node(\"%s\"): %s" % (self.node.dn, self.msg)

class Node:
    """Class representing a node in the database"""

    _attributes_failed = "Unable to obtain attributes for: %s"
    _no_such_attribute = "%s has no such attribute: %s"
    _attribute_has_no_such_value = "Attribute %s does not contain value: %s"
    _set_attribute_called_without_values = "Need to specify either an old value or a new value."

    def __init__ (self, con, dn, attributes = None):
        logger.info ("Creating Node with DN=[%s]" % dn)
        self.con = con
        self.parent = None
        self._children = None
        self._relativeChildren = None

        try:
            self.dn = connection.dn2str(connection.str2dn(dn))
        except exceptions.DNDecodingError:
            raise exceptions.DNDecodingError (dn)

        # If we were'n given a dn, then we populate the Node with the roots
        if not self.dn:
            logger.debug ("Populating root node with roots: %s" % self.con.roots)
            self._children = {}
            for root in self.con.roots:
                try:
                    node = Node (self.con, root)
                    node.parent = self
                    self._children[root] = node
                except exceptions.NoSuchObject as e:
                    logger.error (e)
                    logger.error ("Skipping root %s" % root)

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

        nodes = self.con.search (self.dn, connection.scopeBase)
        node = nodes[0]
        self.attributes = node[1]
        logger.debug ("Attributes for DN=[%s]: %s" % (self.dn, self.attributes))

    def setAttribute (self, attribute, newValue = None, oldValue = None):
        # Make sure we have enough arguments
        if not newValue and not oldValue:
            raise NodeError (self, Node._set_attribute_called_without_values)

        # Figure out the difference
        newValues = None
        if oldValue:
            # We want to replace or remove something
            if attribute in self.attributes:
                oldValues = self.attributes[attribute]
                if oldValue in oldValues:
                    oldAttrs = {attribute: oldValues}
                    if newValue:
                        # We want to replace an existing value
                        newValues = [newValue if (value == oldValue) else value
                                for value in oldValues]
                        newAttrs = {attribute: newValues}
                    else:
                        # We want to remove an existing value
                        newValues = oldValues[:]
                        newValues.remove (oldValue)
                        newAttrs = {attribute: newValues}
                else:
                    raise NodeError (self, Node._attribute_has_no_such_value %
                            (attribute, oldValue))
            else:
                raise NodeError (self, Node._no_such_attribute %
                            (self.dn, attribute))
        else: # Here we know newValue != None
            # We want to add something
            oldAttrs = {}
            newAttrs = {attribute: newValue}
        
        # Send the modification to the server
        self.con.modify(self.dn, oldAttrs, newAttrs)

        # Change our cached value
        if newValues:
            # The values were changed, but we still have some values left
            self.attributes[attribute] = newValues
        elif oldValue and not newValue:
            # A value was removed, leaving no other values
            del self.attributes[attribute]
        elif newValue and not oldValue:
            # We should add a new value
            if attribute in self.attributes:
                self.attributes[attribute].append(newValue)
            else:
                self.attributes[attribute] = [newValue]

    def delete (self):
        try:
            children = self.children
        except exceptions.NoSuchObject:
            return

        # Delete any children this Node has
        for child in children:
            child.delete ()

        # Delete itself, handle quietly the case when Node does not exists
        try:
            self.con.delete (self.dn)
        except exceptions.NoSuchObject:
            logger.warning ("Trying to delete non-existent Node: %s" % self.dn)

        # If this Node has a parent, remove this Node from its list
        key = self.relativeDN()
        if self.parent and key in self.parent._children:
            del self.parent._children[key]

    def add (self, rdn, attr):
        dn = "%s,%s" % (rdn, self.dn)
        self.con.add (dn, attr)
        self._insertChild (dn)

    @property
    def children (self):
        self._populateChildren()
        return self._children.values()

    @property
    def relativeChildren (self):
        self._populateChildren()
        return self._children

    def _populateChildren (self):
        if self._children is None:
            self._children = {}
            children = self.con.search (self.dn, connection.scopeOneLevel)
            for child in children:
                self._insertChild (child[0], child[1])

            logger.debug ("Populated DN=[%s] with children: %s" % (self.dn, self._children))

    def _insertChild (self, dn, attr = None):
        node = Node (self.con, dn, attr)
        node.parent = self
        self._children[node.relativeDN()] = node


    def relativeDN (self, to = None):
        if not to:
            if self.parent:
                to = self.parent
            else:
                to = ""

        toDN = connection.str2dn (str(to))
        myDN = connection.str2dn (self.dn)

        for dn in reversed (toDN):
            if dn == myDN[-1]:
                myDN.pop()
            else:
                break

        return connection.dn2str (myDN)

    def __str__ (self):
        return self.dn

