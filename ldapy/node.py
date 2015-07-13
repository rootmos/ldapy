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

import logging
logger = logging.getLogger("ldapy.%s" % __name__)

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
        except connection.DNDecodingError:
            raise DNError (dn)

        # If we were'n given a dn, then we populate the Node with the roots
        if not self.dn:
            logger.debug ("Populating root node with roots: %s" % self.con.roots)
            self._children = []
            for root in self.con.roots:
                try:
                    node = Node (self.con, root)
                    node.parent = self
                    self._children.append (node)
                except NodeError as e:
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

        try:
            nodes = self.con.search (self.dn, connection.scopeBase)
            node = nodes[0]
            self.attributes = node[1]
            logger.debug ("Attributes for DN=[%s]: %s" % (self.dn, self.attributes))
        except connection.NoSuchOject:
            raise NodeError (self, Node._dn_does_not_exist % self.dn)

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
        logger.debug ("Deleting node with DN: %s" % self.dn)
        self.con.delete (self.dn)

    @property
    def children (self):
        if self._children is None:
            self._children = []
            children = self.con.search (self.dn, connection.scopeOneLevel)
            for child in children:
                node = Node (self.con, child[0], child[1])
                node.parent = self
                self._children.append (node)

            logger.debug ("Populated DN=[%s] with children: %s" % (self.dn, self._children))

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

