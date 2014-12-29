import unittest
import mock
import configuration

from ldapy import Ldapy, NoSuchDN, AlreadyAtRoot


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

    def test_change_DN_up_one_level (self):
        ldapy = Ldapy (self.con)

        root = "dc=nodomain"
        child = "ou=People"

        ldapy.changeDN (root)
        ldapy.changeDN (child)
        self.assertEqual (ldapy.cwd, "%s,%s" % (child, root))

        ldapy.goUpOneLevel ()
        self.assertEqual (ldapy.cwd, root)

    def test_getAttributes_self_and_parent (self):
        ldapy = Ldapy (self.con)

        root = "dc=nodomain"
        child = "ou=People"
        ldapy.changeDN (root)
        ldapy.changeDN (child)

        self.assertIn ("organizationalUnit", ldapy.getAttributes (".")["objectClass"])
        self.assertIn ("top", ldapy.getAttributes ("..")["objectClass"])

    def test_superroot_has_empty_attributes (self):
        ldapy = Ldapy (self.con)
        self.assertDictEqual ({}, ldapy.attributes)


class ChildCompleter (unittest.TestCase):

    def setUp (self):
        self.con = configuration.getConnection ()
        self.ldapy = Ldapy (self.con)
        root = "dc=nodomain"
        self.ldapy.changeDN (root)
        
        self.child1 = "ou=People"
        self.child2 = "ou=Groups"

    def test_empty_input (self):
        matches = self.ldapy.completeChild ("")
        self.assertListEqual (matches, [self.child1, self.child2])

    def test_matches_several (self):
        matches = self.ldapy.completeChild ("ou=")
        self.assertListEqual (matches, [self.child1, self.child2])

    def test_matches_unique (self):
        matches = self.ldapy.completeChild (self.child1[:-1])
        self.assertListEqual (matches, [self.child1])

        matches = self.ldapy.completeChild (self.child2[:-1])
        self.assertListEqual (matches, [self.child2])

    def test_no_matches (self):
        matches = self.ldapy.completeChild ("dc=nonexistent")
        self.assertListEqual (matches, [])


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

    def test_up_one_level_too_far (self):
        ldapy = Ldapy (self.con)

        with self.assertRaises(AlreadyAtRoot) as received:
            ldapy.goUpOneLevel ()

        expected = AlreadyAtRoot ()
        self.assertEqual (str(received.exception), str(expected))

class ArgumentParserTests (unittest.TestCase):
    def setUp (self):
        self.con = configuration.getConnection ()

    def test_successful_parse_with_host (self):
        ldapy = Ldapy (self.con)

        host = "localhost"
        port = 7
        bind_dn = "cn=admin"
        password = "foobar"
        args = ["-H", host, "-p", str(port), "-D", bind_dn, "-w", password]

        self.assertTrue (ldapy.parseArguments (args))
        self.assertEqual (ldapy.args.host, host)
        self.assertEqual (ldapy.args.port, port)
        self.assertEqual (ldapy.args.bind_dn, bind_dn)
        self.assertEqual (ldapy.args.password, password)

    def test_successful_parse_with_uri (self):
        ldapy = Ldapy (self.con)

        host = "localhost"
        port = 7
        bind_dn = "cn=admin"
        password = "foobar"
        args = ["ldap://%s:%s" % (host, port), "-D", bind_dn, "-w", password]

        self.assertTrue (ldapy.parseArguments (args))
        self.assertEqual (ldapy.args.host, host)
        self.assertEqual (ldapy.args.port, port)
        self.assertEqual (ldapy.args.bind_dn, bind_dn)
        self.assertEqual (ldapy.args.password, password)


    def test_neither_host_nor_uri_is_specified (self):
        ldapy = Ldapy (self.con)

        with mock.patch('argparse.ArgumentParser.error') as error_mock:
            ldapy.parseArguments ([])

        error_mock.assert_called_with (Ldapy._neither_host_nor_uri_given)

    def test_both_host_and_uri_is_specified (self):
        ldapy = Ldapy (self.con)

        with mock.patch('argparse.ArgumentParser.error') as error_mock:
            ldapy.parseArguments (["-H", "foo", "ldap://bar"])

        error_mock.assert_called_with (Ldapy._both_host_and_uri_given)

    def test_malformed_uri (self):
        ldapy = Ldapy (self.con)

        with mock.patch('argparse.ArgumentParser.error') as error_mock:
            ldapy.parseArguments (["foobar://lars"])

        error_mock.assert_called_with (Ldapy._uri_malformed)

    def test_port_invalid_number (self):
        ldapy = Ldapy (self.con)

        with mock.patch('argparse.ArgumentParser.error') as error_mock:
            ldapy.parseArguments (["-H", "foo", "-p", "-1"])

        error_mock.assert_called_with (Ldapy._port_is_not_a_valid_number)
        error_mock.reset_mock ()

        with mock.patch('argparse.ArgumentParser.error') as error_mock:
            ldapy.parseArguments (["-H", "foo", "-p", str(0xffff + 1)])

        error_mock.assert_called_with (Ldapy._port_is_not_a_valid_number)
