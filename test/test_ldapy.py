import unittest
import configuration

from ldapy import Ldapy, NoSuchDN


class BasicLdapyTests (unittest.TestCase):
    def setUp (self):
        self.con = configuration.getConnection ()


    def test_list_roots (self):
        ldapy = Ldapy (self.con)
        self.assertIn ("dc=nodomain", ldapy.children)

    def test_change_DN_to_root (self):
        ldapy = Ldapy (self.con)

        root = "dc=nodomain"
        ldapy.changeDN (root)

        self.assertEqual (root, ldapy.cwd)
        self.assertIn ("top", ldapy.attributes["objectClass"])


class ErrorLdapyTests (unittest.TestCase):
    def setUp (self):
        self.con = configuration.getConnection ()

    def test_change_DN_to_nonexistent_root (self):
        ldapy = Ldapy (self.con)

        nonexistent = "dc=nonexistent"

        with self.assertRaises(NoSuchDN) as received:
            ldapy.changeDN (nonexistent)

        expected = NoSuchDN (nonexistent, None)
        self.assertEqual (str(received.exception), str(expected))

    def test_change_DN_to_nonexistent_child (self):
        ldapy = Ldapy (self.con)
        root = "dc=nodomain"
        ldapy.changeDN (root)

        nonexistent = "ou=Foobar"
        with self.assertRaises(NoSuchDN) as received:
            ldapy.changeDN (nonexistent)

        expected = NoSuchDN (nonexistent, root)
        self.assertEqual (str(received.exception), str(expected))
