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

