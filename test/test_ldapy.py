import unittest
import mock
import configuration

from ldapy.ldapy import Ldapy, NoSuchDN, AlreadyAtRoot


class BasicLdapyTests (unittest.TestCase):
    def setUp (self):
        self.con = configuration.getConnection ()

    def getLdapyAtRoot (self):
        with configuration.provision() as p:
            ldapy = Ldapy(self.con)
            self.root = p.root
            ldapy.changeDN (self.root)
            return ldapy

    def test_list_roots (self):
        ldapy = Ldapy (self.con)
        with configuration.provision() as p:
            self.assertIn (p.root, ldapy.children)

    def test_change_DN_to_root (self):
        ldapy = Ldapy(self.con)

        with configuration.provision() as p:
            root = p.root
            ldapy.changeDN (root)

            self.assertEqual (root, ldapy.cwd)
            self.assertIn ("top", ldapy.attributes["objectClass"])

    def test_change_DN_up_one_level (self):
        ldapy = self.getLdapyAtRoot()
        with configuration.provision() as p:
            c1 = p.container()
            ldapy.changeDN(c1.rdn)

            c2 = p.container(c1)
            ldapy.changeDN(c2.rdn)

            self.assertEqual (ldapy.cwd, c2.dn)

            ldapy.goUpOneLevel ()
            self.assertEqual (ldapy.cwd, c1.dn)

    def test_getAttributes_self_and_parent (self):
        ldapy = self.getLdapyAtRoot()
        with configuration.provision() as p:
            c1 = p.container(dnComponent="o", objectClass="organization")
            ldapy.changeDN(c1.rdn)

            c2 = p.container(c1)
            ldapy.changeDN(c2.rdn)

            self.assertIn (c2.objectClass, ldapy.getAttributes (".")["objectClass"])
            self.assertIn (c1.objectClass, ldapy.getAttributes ("..")["objectClass"])

    def test_superroot_has_empty_attributes (self):
        ldapy = Ldapy (self.con)
        self.assertDictEqual ({}, ldapy.attributes)


class ChildCompleter (unittest.TestCase):
    def setUp (self):
        self.con = configuration.getConnection ()

    def getLdapyAtRoot (self):
        with configuration.provision() as p:
            ldapy = Ldapy(self.con)
            self.root = p.root
            ldapy.changeDN (self.root)
            return ldapy

    def test_empty_input (self):
        ldapy = self.getLdapyAtRoot()
        with configuration.provision() as p:
            c = p.container()
            ldapy.changeDN(c.rdn)

            l1 = p.leaf(c)
            l2 = p.leaf(c)

            matches = ldapy.completeChild ("")
            self.assertListEqual(sorted([l1.rdn, l2.rdn]), sorted(matches))

    def test_matches_several (self):
        ldapy = self.getLdapyAtRoot()
        with configuration.provision() as p:
            c = p.container()
            ldapy.changeDN(c.rdn)

            c0 = p.container(c)
            l1 = p.leaf(c)
            l2 = p.leaf(c)

            matches = ldapy.completeChild ("%s=" % l1.dnComponent)
            self.assertListEqual(sorted([l1.rdn, l2.rdn]), sorted(matches))

    def test_matches_unique (self):
        ldapy = self.getLdapyAtRoot()
        with configuration.provision() as p:
            c = p.container()
            ldapy.changeDN(c.rdn)

            l1 = p.leaf(c)
            l2 = p.leaf(c)

            matches = ldapy.completeChild (l1.rdn[:-1])
            self.assertListEqual (matches, [l1.rdn])

            matches = ldapy.completeChild (l2.rdn[:-1])
            self.assertListEqual (matches, [l2.rdn])

    def test_no_matches (self):
        matches = Ldapy(self.con).completeChild ("dc=nonexistent")
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
        with configuration.provision() as p:
            ldapy = Ldapy (self.con)
            ldapy.changeDN (p.root)

            nonexistent = "ou=Foobar"
            with self.assertRaises(NoSuchDN) as received:
                ldapy.changeDN (nonexistent)

            expected = NoSuchDN (nonexistent, p.root)
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
