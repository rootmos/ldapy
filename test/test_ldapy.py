import unittest
import mock
import configuration
from ldapy.node import NodeError
from ldapy.ldapy import Ldapy, AlreadyAtRoot, SetAttributeError, DeleteError
from ldapy.exceptions import NoSuchObject, NoSuchObjectInRoot
import io
import tempfile
from ldapy.connection_data import *

class BasicLdapyTests (unittest.TestCase):
    def setUp (self):
        self.con = configuration.getConnection ()

        # Prepare by setting the historyFile to a temporary file
        self.historyFile = tempfile.NamedTemporaryFile()
        ConnectionDataManager.filename = self.historyFile.name

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

    def test_setAttribute_calls_setAttribute_on_node (self):
        ldapy = self.getLdapyAtRoot()
        with configuration.provision() as p, \
                mock.patch('ldapy.node.Node.setAttribute', autospec=True) as setterMock:
            l = p.leaf()

            attribute = "description"
            oldValue = "test_setAttribute_calls_setAttribute_on_node_old"
            newValue = "test_setAttribute_calls_setAttribute_on_node_new"

            child = ldapy._resolveRelativeDN (l.rdn)
            ldapy.setAttribute (l.rdn, attribute,
                    newValue = newValue, oldValue = oldValue)
            setterMock.assert_called_once_with (child, attribute,
                    newValue = newValue, oldValue = oldValue)

    def test_delete_calls_delete_on_node (self):
        ldapy = self.getLdapyAtRoot()
        with configuration.provision() as p,\
                mock.patch('ldapy.node.Node.delete', autospec=True) as deleteMock:
            l = p.leaf()

            child = ldapy._resolveRelativeDN (l.rdn)
            ldapy.delete (l.rdn)

            deleteMock.assert_called_once_with (child)

    def test_add_calls_add_on_node (self):
        ldapy = self.getLdapyAtRoot()
        with mock.patch('ldapy.node.Node.add', autospec=True) as addMock:
            cwd = ldapy._resolveRelativeDN (".")
            rdn = "cn=Foo"
            attr = {"objectClass": "Bar"}
            ldapy.add (rdn, attr)

            addMock.assert_called_once_with (cwd, rdn, attr)

    def test_successful_connection_calls_addRecentConnection (self):
        connectionData = ConnectionData (configuration.uri,
                configuration.admin,
                configuration.admin_password)
        with mock.patch("ldapy.ldapy.Ldapy.parseArguments", autospec=True) as parseArgumentsMock,\
                mock.patch("ldapy.connection_data.ConnectionDataManager.addRecentConnection", autospec=True) as addRecentConnectionMock:
            parseArgumentsMock.return_value = (connectionData, True)

            ldapy = Ldapy()

        addRecentConnectionMock.assert_called_once_with (ldapy._lazyConnectionDataManager, connectionData)

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

        # Prepare by setting the historyFile to a temporary file
        self.historyFile = tempfile.NamedTemporaryFile()
        ConnectionDataManager.filename = self.historyFile.name

    def getLdapyAtRoot (self):
        with configuration.provision() as p:
            ldapy = Ldapy(self.con)
            self.root = p.root
            ldapy.changeDN (self.root)
            return ldapy

    def test_change_DN_to_nonexistent_root (self):
        ldapy = Ldapy (self.con)

        nonexistent = "dc=nonexistent"

        with self.assertRaises(NoSuchObjectInRoot) as received:
            ldapy.changeDN (nonexistent)

        expected = NoSuchObjectInRoot (nonexistent)
        self.assertEqual (str(received.exception), str(expected))

    def test_change_DN_to_nonexistent_child (self):
        with configuration.provision() as p:
            ldapy = Ldapy (self.con)
            ldapy.changeDN (p.root)

            nonexistentRDN = "ou=Foobar"
            nonexistent = "%s,%s" % (nonexistentRDN, p.root)
            with self.assertRaises(NoSuchObject) as received:
                ldapy.changeDN (nonexistentRDN)

            expected = NoSuchObject (nonexistent)
            self.assertEqual (str(received.exception), str(expected))

    def test_up_one_level_too_far (self):
        ldapy = Ldapy (self.con)

        with self.assertRaises(AlreadyAtRoot) as received:
            ldapy.goUpOneLevel ()

        expected = AlreadyAtRoot ()
        self.assertEqual (str(received.exception), str(expected))

    def test_NoSuchObject_for_setAttribute (self):
        ldapy = self.getLdapyAtRoot()
        nonexistentRDN = "dc=nonexistent"
        nonexistent = "%s,%s" % (nonexistentRDN, ldapy.cwd)
        attribute = "description"

        with self.assertRaises(NoSuchObject) as received:
            ldapy.setAttribute (nonexistentRDN, attribute)

        expected = NoSuchObject (nonexistent)
        self.assertEqual (str(received.exception), str(expected))

    def test_setAttribute_errors_are_propagated (self):
        ldapy = self.getLdapyAtRoot()
        with configuration.provision() as p:
            l = p.leaf()
            
            testMessage = "test_setAttribute_errors_are_propagated_msg"
            with mock.patch('ldapy.node.Node.setAttribute',
                    side_effect=NodeError(None, testMessage)):

                with self.assertRaises(SetAttributeError) as received:
                    ldapy.setAttribute (l.rdn, "attribute")

            self.assertEqual (received.exception.msg, testMessage)
            self.assertEqual (str(received.exception), testMessage)

    def test_NoSuchObject_for_delete (self):
        ldapy = self.getLdapyAtRoot()
        nonexistentRDN = "dc=nonexistent"
        nonexistent = "%s,%s" % (nonexistentRDN, ldapy.cwd)

        with self.assertRaises(NoSuchObject) as received:
            ldapy.delete (nonexistentRDN)

        expected = NoSuchObject (nonexistent)
        self.assertEqual (str(received.exception), str(expected))

    def test_delete_errors_are_propagated (self):
        ldapy = self.getLdapyAtRoot()
        with configuration.provision() as p:
            l = p.leaf()

            testMessage = "test_delete_errors_are_propagated_msg"
            with mock.patch('ldapy.node.Node.delete',
                    side_effect=NodeError(None, testMessage)):

                with self.assertRaises(DeleteError) as received:
                    ldapy.delete (l.rdn)

            self.assertEqual (received.exception.msg, testMessage)
            self.assertEqual (str(received.exception), testMessage)

    def test_failed_connection_does_not_call_addRecentConnection (self):
        connectionData = ConnectionData ("ldap://foo", configuration.admin, configuration.admin_password)
        with mock.patch("ldapy.ldapy.Ldapy.parseArguments", autospec=True) as parseArgumentsMock,\
                mock.patch("ldapy.connection_data.ConnectionDataManager.addRecentConnection", autospec=True) as addRecentConnectionMock:
            parseArgumentsMock.return_value = (connectionData, True)

            try:
                ldapy = Ldapy()

                # Expect that Ldapy's constructor calls sys.exit
                self.assertTrue(False)
            except SystemExit:
                self.assertFalse (addRecentConnectionMock.called)


class ArgumentParserTests (unittest.TestCase):
    def setUp (self):
        self.con = configuration.getConnection ()

        # Prepare by setting the historyFile to a temporary file
        self.historyFile = tempfile.NamedTemporaryFile()
        ConnectionDataManager.filename = self.historyFile.name

    def test_successful_parse_with_host (self):
        ldapy = Ldapy (self.con)

        host = "localhost"
        port = 7
        uri = "ldap://%s:%u" % (host, port)
        bind_dn = "cn=admin"
        password = "foobar"
        args = ["-H", host, "-p", str(port), "-D", bind_dn, "-w", password]

        connectionData, _ = ldapy.parseArguments (args)
        self.assertEqual (connectionData.uri, uri)
        self.assertEqual (connectionData.bind_dn, bind_dn)
        self.assertEqual (connectionData.password, password)

    def test_successful_parse_with_uri (self):
        ldapy = Ldapy (self.con)

        host = "localhost"
        port = 7
        uri = "ldap://%s:%u" % (host, port)
        bind_dn = "cn=admin"
        password = "foobar"
        args = ["ldap://%s:%s" % (host, port), "-D", bind_dn, "-w", password]

        connectionData, _ = ldapy.parseArguments (args)
        self.assertEqual (connectionData.uri, uri)
        self.assertEqual (connectionData.bind_dn, bind_dn)
        self.assertEqual (connectionData.password, password)

    def test_neither_host_nor_uri_is_specified (self):
        ldapy = Ldapy (self.con)

        with mock.patch('sys.stderr', new_callable=io.BytesIO) as output,\
                self.assertRaises(SystemExit) as e:
                    ldapy.parseArguments ([])

        self.assertIn(ldapy._neither_host_nor_uri_given, output.getvalue())
        self.assertEqual(e.exception.code, 2)

    def test_both_host_and_uri_is_specified (self):
        ldapy = Ldapy (self.con)

        with mock.patch('sys.stderr', new_callable=io.BytesIO) as output,\
                self.assertRaises(SystemExit) as e:
                    ldapy.parseArguments (["-H", "foo", "ldap://bar"])

        self.assertIn(ldapy._both_host_and_uri_given, output.getvalue())
        self.assertEqual(e.exception.code, 2)

    def test_malformed_uri (self):
        ldapy = Ldapy (self.con)

        with mock.patch('sys.stderr', new_callable=io.BytesIO) as output,\
                self.assertRaises(SystemExit) as e:
                    ldapy.parseArguments (["foobar://lars"])

        self.assertIn(ldapy._uri_malformed, output.getvalue())
        self.assertEqual(e.exception.code, 2)

    def test_port_invalid_number (self):
        ldapy = Ldapy (self.con)

        with mock.patch('sys.stderr', new_callable=io.BytesIO) as output,\
                self.assertRaises(SystemExit) as e:
                    ldapy.parseArguments (["-H", "foo", "-p", "-1"])

        self.assertIn(ldapy._port_is_not_a_valid_number, output.getvalue())
        self.assertEqual(e.exception.code, 2)

        with mock.patch('sys.stderr', new_callable=io.BytesIO) as output,\
                self.assertRaises(SystemExit) as e:
                    ldapy.parseArguments (["-H", "foo", "-p", str(0xffff + 1)])

        self.assertIn(ldapy._port_is_not_a_valid_number, output.getvalue())
        self.assertEqual(e.exception.code, 2)


    def test_previous_connection (self):
        ldapy = Ldapy (self.con)
        getter = mock.create_autospec (ldapy.connectionDataManager.getRecentConnection)
        getter.return_value = {}
        ldapy.connectionDataManager.getRecentConnection = getter

        N = 7
        connectionData, new = ldapy.parseArguments (["--previous", str(N)])

        getter.assert_called_once_with (N)
        self.assertIs (connectionData, getter.return_value)
        self.assertFalse (new)

    def test_no_such_previous_connection (self):
        ldapy = Ldapy (self.con)

        N = 7
        with mock.patch ('sys.stderr', new_callable=io.BytesIO) as output,\
                self.assertRaises(SystemExit) as e:
                    ldapy.parseArguments (["--previous", str(N)])

        msg = str(NoSuchRecentConnection(N))
        self.assertIn (msg, output.getvalue())
        self.assertEqual (e.exception.code, 3)

    def test_list_previous_connections (self):
        ldapy = Ldapy (self.con)
        getter = mock.create_autospec (ldapy.connectionDataManager.getRecentConnections)
        ldapy.connectionDataManager.getRecentConnections = getter

        a = ConnectionData("ldap://a.com", "cn=a")
        b = ConnectionData("ldap://b.com", "cn=b")
        getter.return_value = [a, b]

        with mock.patch ('sys.stdout', new_callable=io.BytesIO) as output,\
                self.assertRaises(SystemExit) as e:
                    ldapy.parseArguments (["-P"])

        self.assertEqual (e.exception.code, 0)

        lines = output.getvalue().splitlines()
        self.assertIn (a.uri, lines[0])
        self.assertIn (a.bind_dn, lines[0])

        self.assertIn (b.uri, lines[1])
        self.assertIn (b.bind_dn, lines[1])

    def test_previous_connection_with_too_many_arguments (self):
        ldapy = Ldapy (self.con)
        with mock.patch ('sys.stderr', new_callable=io.BytesIO) as output,\
                self.assertRaises(SystemExit) as e:
                    ldapy.parseArguments (["--previous", "6", "7"])

        self.assertEqual (e.exception.code, 2)
        self.assertIn (ldapy._too_many_arguments, output.getvalue())


    def test_saved_connection (self):
        ldapy = Ldapy (self.con)
        getter = mock.create_autospec (ldapy.connectionDataManager.getConnection)
        getter.return_value = {}
        ldapy.connectionDataManager.getConnection = getter

        name = "foo"
        connectionData, new = ldapy.parseArguments (["--saved", name])

        getter.assert_called_once_with (name)
        self.assertIs (connectionData, getter.return_value)
        self.assertFalse (new)

    def test_no_such_saved_connection (self):
        ldapy = Ldapy (self.con)

        name = "foo"
        with mock.patch ('sys.stderr', new_callable=io.BytesIO) as output,\
                self.assertRaises(SystemExit) as e:
                    ldapy.parseArguments (["-S", name])

        msg = str(NoSuchSavedConnection(name))
        self.assertIn (msg, output.getvalue())
        self.assertEqual (e.exception.code, 3)

    def test_list_saved_connections (self):
        ldapy = Ldapy (self.con)
        getter = mock.create_autospec (ldapy.connectionDataManager.getConnections)
        ldapy.connectionDataManager.getConnections = getter

        nameA = "nameA"
        a = ConnectionData("ldap://a.com", "cn=a")

        nameB = "nameB"
        b = ConnectionData("ldap://b.com", "cn=b")

        getter.return_value = {nameA:a, nameB:b}

        with mock.patch ('sys.stdout', new_callable=io.BytesIO) as output,\
                self.assertRaises(SystemExit) as e:
                    ldapy.parseArguments (["--saved"])

        self.assertEqual (e.exception.code, 0)

        lines = output.getvalue().splitlines()
        self.assertIn (nameA, lines[0])
        self.assertIn (a.uri, lines[0])
        self.assertIn (a.bind_dn, lines[0])

        self.assertIn (nameB, lines[1])
        self.assertIn (b.uri, lines[1])
        self.assertIn (b.bind_dn, lines[1])

    def test_saved_connection_with_too_many_arguments (self):
        ldapy = Ldapy (self.con)
        with mock.patch ('sys.stderr', new_callable=io.BytesIO) as output,\
                self.assertRaises(SystemExit) as e:
                    ldapy.parseArguments (["--saved", "foo", "bar"])

        self.assertEqual (e.exception.code, 2)
        self.assertIn (ldapy._too_many_arguments, output.getvalue())



    def test_save_connection (self):
        ldapy = Ldapy (self.con)

        getter = mock.create_autospec (ldapy.connectionDataManager.getRecentConnection)
        getter.return_value = {}
        ldapy.connectionDataManager.getRecentConnection = getter

        saver = mock.create_autospec (ldapy.connectionDataManager.saveConnection)
        ldapy.connectionDataManager.saveConnection = saver

        N = 7
        name = "foo"
        with self.assertRaises(SystemExit) as e:
            ldapy.parseArguments (["--save", str(N), name])

        self.assertEqual (e.exception.code, 0)
        getter.assert_called_once_with (N)
        saver.assert_called_once_with (name, getter.return_value)

    def test_save_with_no_such_connection (self):
        ldapy = Ldapy (self.con)

        N = 7
        name = "foo"
        with mock.patch ('sys.stderr', new_callable=io.BytesIO) as output,\
                self.assertRaises(SystemExit) as e:
                    ldapy.parseArguments (["--save", str(N), name])

        msg = str(NoSuchRecentConnection(N))
        self.assertIn (msg, output.getvalue())
        self.assertEqual (e.exception.code, 3)

    def test_save_with_not_a_number (self):
        ldapy = Ldapy (self.con)

        with mock.patch ('sys.stderr', new_callable=io.BytesIO) as output,\
                self.assertRaises(SystemExit) as e:
                    ldapy.parseArguments (["--save", "foo", "bar"])

        self.assertIn (Ldapy._first_argument_must_be_a_number, output.getvalue())
        self.assertEqual (e.exception.code, 2)

