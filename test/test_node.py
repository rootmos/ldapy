from ldapy.node import Node, NodeError, DNError
import unittest
import configuration
import provisioning

class BasicNodeTests (unittest.TestCase):
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

class ModifyAttributesTests (unittest.TestCase):
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
            valueStays = "test_remove_value_stays"
            valueGoes = "test_remove_value_goes"

            l = p.leaf(attr={attribute: [valueStays, valueGoes]})
            node = Node (self.con, l.dn)
            node.setAttribute (attribute, oldValue = valueGoes, newValue = None)

            self.assertListEqual([valueStays], p.attribute(l, attribute))
            self.assertListEqual([valueStays], node.attributes[attribute])

class NodeErrors (unittest.TestCase):
    def setUp (self):
        self.con = configuration.getConnection ()

    def test_malformed_dn (self):
        malformed_dn = "malformed"
        with self.assertRaises (DNError) as received:
            node = Node (self.con, malformed_dn)

        msg = DNError._malformed_dn_message % malformed_dn
        self.assertTrue (msg in str(received.exception))

    def test_dn_does_not_exist (self):
        bad_dn = "dc=does_not_exist"
        with self.assertRaises (NodeError) as received:
            node = Node (self.con, bad_dn)

        msg = Node._dn_does_not_exist % bad_dn
        self.assertTrue (msg in str(received.exception))

if __name__ == '__main__':
    unittest.main()
