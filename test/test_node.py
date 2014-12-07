from node import Node, NodeError, DNError
import unittest
import configuration

class NodeErrors (unittest.TestCase):

    def setUp (self):
        self.con = configuration.getConnection ()

    def test_malformed_dn (self):
        malformed_dn = "malformed"
        with self.assertRaises (DNError) as received:
            node = Node (self.con, malformed_dn)

    def test_dn_does_not_exist (self):
        bad_dn = "dn=does_not_exist"
        with self.assertRaises (NodeError) as received:
            node = Node (self.con, bad_dn)
        
        msg = Node._dn_does_not_exist % bad_dn
        expected = ConnectionError (con, msg)
        self.assertEqual (str(received.exception), str(expected))


