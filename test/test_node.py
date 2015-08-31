from ldapy.node import Node, NodeError
from ldapy.exceptions import LdapError, DNDecodingError, NoSuchObject, UndefinedType, TypeOrValueExists
import unittest2
import mock
import configuration
import provisioning

class BasicNodeTests (unittest2.TestCase):
    def setUp (self):
        self.con = configuration.getConnection ()

    def test_successful_creation (self):
        with configuration.provision() as p:
            l = p.leaf()
            longDN = l.dn.replace(",", ", ")

            node = Node (self.con, longDN)

            self.assertEqual (node.dn, l.dn)
            self.assertIsNotNone (node.attributes)

    def test_attributes (self):
        with configuration.provision() as p:
            l = p.leaf(attr={"description":"test_attributes"})
            node = Node (self.con, l.dn)
            self.assertEqual (node.attributes["description"][0], "test_attributes")

    def test_children (self):
        with configuration.provision() as p:
            c = p.container()
            l = p.leaf(c, attr={"description":"test_children"})

            parent = Node (self.con, c.dn)

            children = parent.children
            self.assertEqual (len(children), 1)

            child = children[0]
            self.assertEqual (child.dn, l.dn)
            self.assertEqual (child.parent, parent)
            self.assertEqual (child.attributes["description"][0], "test_children")

    def test_relative_parent (self):
        with configuration.provision() as p:
            c = p.container()
            l = p.leaf(c)
            
            parent = Node (self.con, c.dn)

            child = parent.children[0]
            assert child.relativeDN () == l.rdn

    def test_relative_superparent (self):
        with configuration.provision() as p:
            c = p.container()
            l = p.leaf(c)

            leaf = Node (self.con, l.dn)
            rdn = l.rdn + "," + c.rdn
            self.assertEqual(leaf.relativeDN (c.parent), rdn)

    def test_relative_out_of_tree (self):
        with configuration.provision() as p:
            l = p.leaf()
            leaf = Node (self.con, l.dn)
            assert leaf.relativeDN ("dc=out_of_tree") == str (leaf)

    def test_relative_children (self):
        with configuration.provision() as p:
            c = p.container()
            l1 = p.leaf(c)
            l2 = p.leaf(c)
            
            node = Node (self.con, c.dn)

            expect = [l1.rdn, l2.rdn]
            relative = node.relativeChildren.keys ()
            for e in expect:
                self.assertIn (e, relative)

class ModifyAttributesTests (unittest2.TestCase):
    def setUp (self):
        self.con = configuration.getConnection ()

    def test_simple_replace (self):
        with configuration.provision() as p:
            attribute = "description"
            newValue = "test_simple_replace_new"
            oldValue = "test_simple_replace_old"

            l = p.leaf(attr={attribute: oldValue})

            node = Node (self.con, l.dn)
            node.setAttribute (attribute, newValue, oldValue = oldValue)

            self.assertListEqual([newValue], p.attribute(l, attribute))
            self.assertListEqual([newValue], node.attributes[attribute])

    def test_must_attribute_replace (self):
        with configuration.provision() as p:
            objectClass = "person"
            mustAttribute = "sn"
            newValue = "test_must_attribute_replace_new"
            oldValue = "test_must_attribute_replace_old"

            l = p.leaf(attr={mustAttribute: oldValue}, objectClass=objectClass)

            node = Node (self.con, l.dn)
            node.setAttribute (mustAttribute, newValue, oldValue = oldValue)

            self.assertListEqual([newValue], p.attribute(l, mustAttribute))
            self.assertListEqual([newValue], node.attributes[mustAttribute])

    def test_replace_one_value_of_two (self):
        with configuration.provision() as p:
            attribute = "description"
            newValue = "test_replace_one_value_of_two_new"
            oldValue = "test_replace_one_value_of_two_old"
            additionalValue = "test_replace_one_value_of_two_another_value"

            l = p.leaf(attr={attribute: [oldValue, additionalValue]})

            node = Node (self.con, l.dn)
            node.setAttribute (attribute, newValue, oldValue = oldValue)

            self.assertListEqual(sorted([newValue, additionalValue]),
                                 sorted(p.attribute(l, attribute)))
            self.assertListEqual(sorted([newValue, additionalValue]),
                                 sorted(node.attributes[attribute]))

    def test_add_new_attribute (self):
        with configuration.provision() as p:
            attribute = "description"
            newValue = "test_add_new_attribute"

            l = p.leaf()
            self.assertListEqual([], p.attribute(l, attribute))

            node = Node (self.con, l.dn)
            node.setAttribute (attribute, newValue)

            self.assertListEqual([newValue], p.attribute(l, attribute))
            self.assertListEqual([newValue], node.attributes[attribute])
    
    def test_add_value_to_existing_attribute (self):
        with configuration.provision() as p:
            attribute = "description"
            newValue = "test_add_value_to_existing_attribute_new"
            oldValue = "test_add_value_to_existing_attribute_old"

            l = p.leaf(attr={attribute: oldValue})

            node = Node (self.con, l.dn)
            node.setAttribute (attribute, newValue)

            self.assertListEqual(sorted([newValue, oldValue]),
                                 sorted(p.attribute(l, attribute)))
            self.assertListEqual(sorted([newValue, oldValue]),
                                 sorted(node.attributes[attribute]))

    def test_add_undefined_attribute (self):
        with configuration.provision() as p:
            attribute = "foo"
            newValue = "bar"

            l = p.leaf()

            node = Node (self.con, l.dn)
            with self.assertRaises (UndefinedType) as received:
                node.setAttribute (attribute, newValue)

            self.assertIn (attribute, str(received.exception))

    def test_add_existing_value (self):
        with configuration.provision() as p:
            attribute = "description"
            value = "test_add_existing_value"

            l = p.leaf(attr={attribute:value})

            node = Node (self.con, l.dn)
            with self.assertRaises (TypeOrValueExists) as received:
                node.setAttribute (attribute, value)

            self.assertEqual({attribute:value}, received.exception.attributes)
            self.assertIn (value, str(received.exception))

    def test_replace_non_existent_value (self):
        with configuration.provision() as p:
            attribute = "description"
            newValue = "test_replace_non_existent_value_new"
            oldValue = "test_replace_non_existent_value_old"
            nonExistentValue = "non_existent"

            l = p.leaf(attr={attribute: oldValue})

            node = Node (self.con, l.dn)
            with self.assertRaises (NodeError) as received:
                node.setAttribute (attribute, newValue, oldValue = nonExistentValue)
            msg = Node._attribute_has_no_such_value % (attribute, nonExistentValue)
            self.assertTrue (msg in str(received.exception))

    def test_replace_non_existent (self):
        with configuration.provision() as p:
            attribute = "description"
            newValue = "test_replace_non_existent_new"
            oldValue = "test_replace_non_existent_old"
            nonExistentValue = "non_existent"

            l = p.leaf()

            node = Node (self.con, l.dn)
            with self.assertRaises (NodeError) as received:
                node.setAttribute (attribute, newValue, oldValue = nonExistentValue)
            msg = Node._no_such_attribute % (l.dn, attribute)
            self.assertTrue (msg in str(received.exception))

    def test_call_with_no_values (self):
        with configuration.provision() as p:
            attribute = "description"

            l = p.leaf()
            node = Node (self.con, l.dn)

            with self.assertRaises (NodeError) as received:
                node.setAttribute (attribute)
            msg = Node._set_attribute_called_without_values
            self.assertTrue (msg in str(received.exception))

    def test_remove_value (self):
        with configuration.provision() as p:
            attribute = "description"
            valueGoes = "test_remove_value_goes"

            l = p.leaf(attr={attribute: valueGoes})
            node = Node (self.con, l.dn)
            node.setAttribute (attribute, oldValue = valueGoes, newValue = None)

            self.assertListEqual([], p.attribute(l, attribute))
            self.assertTrue(attribute not in node.attributes)

    def test_remove_value_two (self):
        with configuration.provision() as p:
            attribute = "description"
            valueStays = "test_remove_value_stays"
            valueGoes = "test_remove_value_goes"

            l = p.leaf(attr={attribute: [valueStays, valueGoes]})
            node = Node (self.con, l.dn)
            node.setAttribute (attribute, oldValue = valueGoes, newValue = None)

            self.assertListEqual([valueStays], p.attribute(l, attribute))
            self.assertListEqual([valueStays], node.attributes[attribute])

    def test_remove_must_attribute (self):
        with configuration.provision() as p:
            objectClass = "person"
            mustAttribute = "sn"
            valueGoes = "test_must_attribute_replace_old"

            l = p.leaf(attr={mustAttribute: valueGoes}, objectClass=objectClass)
            node = Node (self.con, l.dn)

            with self.assertRaises (LdapError) as received:
                node.setAttribute(mustAttribute, oldValue = valueGoes, newValue = None)


class DeleteTests (unittest2.TestCase):
    def setUp (self):
        self.con = configuration.getConnection ()

    def test_delete_leaf (self):
        with configuration.provision() as p:
            l = p.leaf ()
            self.assertTrue (p.exists(l))

            node = Node (self.con, l.dn)
            node.delete ()

            self.assertFalse (p.exists(l))

    def test_delete_one_leaf (self):
        with configuration.provision() as p:
            l1 = p.leaf ()
            l2 = p.leaf ()
            self.assertTrue (p.exists(l1))
            self.assertTrue (p.exists(l2))

            node = Node (self.con, l1.dn)
            node.delete ()

            self.assertFalse (p.exists(l1))
            self.assertTrue (p.exists(l2))

    def test_delete_empty_container (self):
        with configuration.provision() as p:
            c = p.container ()
            self.assertTrue (p.exists(c))

            node = Node (self.con, c.dn)
            node.delete ()

            self.assertFalse (p.exists(c))

    def test_delete_nonempty_container (self):
        with configuration.provision() as p:
            c = p.container ()
            l = p.leaf (c)

            self.assertTrue (p.exists(c))
            self.assertTrue (p.exists(l))

            node = Node (self.con, c.dn)
            node.delete ()

            self.assertFalse (p.exists(l))
            self.assertFalse (p.exists(c))


    def test_update_children_in_parent_of_deleted_node (self):
        with configuration.provision() as p:
            c = p.container ()
            self.assertTrue (p.exists(c))

            l1 = p.leaf (c)
            l2 = p.leaf (c)

            self.assertTrue (p.exists(l1))
            self.assertTrue (p.exists(l2))

            node = Node (self.con, c.dn)

            expectedChildren = sorted([l1.dn, l2.dn])
            children = sorted([child.dn for child in node.children])
            self.assertListEqual (children, expectedChildren)

            for child in node.children:
                if child.dn == l1.dn:
                    child.delete()
                    break

            expectedChildren = sorted([l2.dn])
            children = sorted([child.dn for child in node.children])
            self.assertListEqual (children, expectedChildren)

            self.assertFalse (p.exists(l1))
            self.assertTrue (p.exists(l2))

    def test_delete_node_twice (self):
        with configuration.provision() as p:
            l = p.leaf ()

            node = Node (self.con, l.dn)

            node.delete()
            node.delete()

    def test_delete_container_with_deleted_node (self):
        with configuration.provision() as p:
            c = p.leaf ()
            l = p.leaf (c)

            self.assertTrue (p.exists(c))
            self.assertTrue (p.exists(l))

            node = Node (self.con, c.dn)

            expectedChildren = sorted([l.dn])
            children = sorted([child.dn for child in node.children])
            self.assertListEqual (children, expectedChildren)


            # Delete the leaf on the server
            p.delete (l)

            # But the Node's blissfully unaware
            expectedChildren = sorted([l.dn])
            children = sorted([child.dn for child in node.children])
            self.assertListEqual (children, expectedChildren)

            self.assertTrue (p.exists(c))
            self.assertFalse (p.exists(l))

            node.delete()

class AddTests (unittest2.TestCase):
    def setUp (self):
        self.con = configuration.getConnection ()

    def test_add_delegates (self):
        with configuration.provision() as p:
            c = p.container ()
            node = Node (self.con, c.dn)

            rdn = "cn=Foo"
            dn = "%s,%s" % (rdn, c.dn)
            attr = {"objectClass": "Bar"}

            # Prohibit the addition of the fake new object
            node._insertChild = mock.create_autospec(node._insertChild)

            with mock.patch ("ldapy.connection.Connection.add", autospec=True) as add_mock:
                node.add (rdn, attr)

            add_mock.assert_called_once_with (self.con, dn, attr)

    def test_add_successful (self):
        with configuration.provision() as p:
            c = p.container ()
            node = Node (self.con, c.dn)

            rdn = "cn=test_add_successful"
            dn = "%s,%s" % (rdn, c.dn)
            attr = {"objectClass": "organizationalRole"}

            # Pre-condition, new object does not exist
            self.assertFalse(p.exists(dn))
            self.assertNotIn(rdn, node.relativeChildren)

            try:
                node.add (rdn, attr)

                # Check that the new object exists
                self.assertTrue(p.exists(dn))
                self.assertIn(rdn, node.relativeChildren)
            finally:
                # Cleanup
                p.delete (dn)

class NodeErrors (unittest2.TestCase):
    def setUp (self):
        self.con = configuration.getConnection ()

    def test_malformed_dn (self):
        malformed_dn = "malformed"
        with self.assertRaises (DNDecodingError) as received:
            node = Node (self.con, malformed_dn)

        msg = DNDecodingError._malformed_dn_message % malformed_dn
        self.assertTrue (msg in str(received.exception))

    def test_dn_does_not_exist (self):
        bad_dn = "dc=does_not_exist"
        with self.assertRaises (NoSuchObject):
            node = Node (self.con, bad_dn)

    def test_non_existing_root_node (self):
        nonexistent="dc=nonexistent"
        with mock.patch ("ldapy.connection.Connection.roots",
                new_callable=mock.PropertyMock,
                return_value=[nonexistent]):
            node = Node (self.con, None)
            self.assertListEqual([], node.children)

if __name__ == '__main__':
    unittest2.main()
