from node import Node, NodeError, DNError
import unittest
import configuration

class BasicNodeTests (unittest.TestCase):
    def setUp (self):
        self.con = configuration.getConnection ()

    def test_successful_creation (self):
        dn_long = "ou=People, dc=nodomain"
        dn_shortened = "ou=People,dc=nodomain"
        node = Node (self.con, dn_long)

        self.assertEqual (node.dn, dn_shortened)
        self.assertIsNotNone (node.attributes)

    def test_attributes (self):
        dn = "ou=People,dc=nodomain"
        node = Node (self.con, dn)

        self.assertEqual (node.attributes["objectClass"][0], "organizationalUnit")

    def test_children (self):
        dn ="ou=People,dc=nodomain"
        parent = Node (self.con, dn)

        children = parent.children
        self.assertEqual (len(children), 1)

        child = children[0]
        self.assertEqual (child.dn, "uid=john,ou=People,dc=nodomain")
        self.assertEqual (child.parent, parent)
        self.assertIn("posixAccount", child.attributes["objectClass"])

    def test_relative_parent (self):
        dn ="ou=People,dc=nodomain"
        parent = Node (self.con, dn)

        child = parent.children[0]

        assert child.relativeDN () == "uid=john"

    def test_relative_superparent (self):
        dn = "uid=john,ou=People,dc=nodomain"
        leaf = Node (self.con, dn)

        assert leaf.relativeDN ("dc=nodomain") == "uid=john,ou=People"

    def test_relative_out_of_tree (self):
        dn = "uid=john,ou=People,dc=nodomain"
        leaf = Node (self.con, dn)

        assert leaf.relativeDN ("dc=out_of_tree") == str (leaf)

    def test_relative_children (self):
        dn = "dc=nodomain"
        node = Node (self.con, dn)

        expect = ["ou=People", "ou=Groups"]
        relative = node.relativeChildren.keys ()
        for e in expect:
            self.assertIn (e, relative)

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
