from node import Node, NodeError, DNError
import unittest
import configuration

class BasicNodeTests (unittest.TestCase):
    def setUp (self):
        self.con = configuration.getConnection ()

    def test_successful_creation (self):
        dn = "ou=People, dc=nodomain"
        dn_shortened = "ou=People,dc=nodomain"
        node = Node (self.con, dn)

        self.assertEqual (node.dn, dn_shortened)
        self.assertIsNotNone (node.attributes)

class NodeErrors (unittest.TestCase):
    def setUp (self):
        self.con = configuration.getConnection ()

    def test_malformed_dn (self):
        malformed_dn = "malformed"
        with self.assertRaises (DNError) as received:
            node = Node (self.con, malformed_dn)

    def test_dn_does_not_exist (self):
        bad_dn = "dc=does_not_exist"
        with self.assertRaises (NodeError) as received:
            node = Node (self.con, bad_dn)
        
        msg = Node._dn_does_not_exist % bad_dn
        self.assertTrue (msg in str(received.exception))

if __name__ == '__main__':
    unittest.main()
