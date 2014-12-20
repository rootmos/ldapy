import unittest
import configuration

from ldapy import Ldapy


class BasicLdapyTests (unittest.TestCase):
    def setUp (self):
        self.con = configuration.getConnection ()


    def test_list_roots (self):
        ldapy = Ldapy (self.con)

        expect = self.con.roots
        print "Expect: ", expect

        got = ldapy.children
        print "Got: ", got

        self.assertListEqual (expect, got)

    def test_change_DN_to_root (self):
        ldapy = Ldapy (self.con)

        root = "dc=nodomain"
        ldapy.changeDN (root)

        self.assertEqual (root, ldapy.cwd)
        self.assertIn ("top", ldapy.attributes["objectClass"])
