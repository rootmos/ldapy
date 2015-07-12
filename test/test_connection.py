from ldapy.connection import Connection, ConnectionError, LdapError, scopeBase
import unittest
import mock
import ldap
import ldap.ldapobject
import configuration

class BasicConnection(unittest.TestCase):

    def setUp (self):
        self.con = Connection (configuration.uri)

    def test_initialization (self):
        self.assertEqual (self.con.uri, configuration.uri)
        self.assertIsInstance (self.con._ldap, ldap.ldapobject.LDAPObject)
        self.assertFalse (self.con.connected)

    def test_bind (self):
        self.con.bind (configuration.admin, configuration.admin_password)
        self.assertTrue (self.con.connected)

class Utilities (unittest.TestCase):
    def setUp (self):
        self.con = Connection (configuration.uri)
        self.con.bind (configuration.admin, configuration.admin_password)
        assert self.con.connected

    def test_find_roots (self):
        with configuration.provision() as p:
            self.assertIn (p.root, self.con.roots)

class ConnectionErrors (unittest.TestCase):

    def test_bind_connect_error (self):
        bad_uri = "ldap://foobar"
        con = Connection (bad_uri)
        with self.assertRaises(ConnectionError) as received:
            con.bind ("", "")

        msg = Connection._connection_error_msg % bad_uri
        expected = ConnectionError (con, msg)
        self.assertEqual (str(received.exception), str(expected))

    def test_bind_auth_error (self):
        bad_user ="cn=badguy,dc=lair"
        bad_password ="urg"
        con = Connection (configuration.uri)
        with self.assertRaises(ConnectionError) as received:
            con.bind (bad_user, bad_password)

        msg = Connection._bad_auth_error_msg % bad_user
        expected = ConnectionError (con, msg)
        self.assertEqual (str(received.exception), str(expected))

    def test_search_passes_on_ldap_errors (self):
        self.con = Connection (configuration.uri)

        expect = ldap.OTHER("Foobar")
        with mock.patch ("ldap.ldapobject.LDAPObject.search_s", side_effect=expect):
            with self.assertRaises (LdapError) as received:
                self.con.search ("dc=root", scopeBase)
            
        self.assertEqual (str(expect), str(received.exception)) 

    def test_modify_passes_on_ldap_errors (self):
        self.con = Connection (configuration.uri)

        expect = ldap.OTHER("Foobar")
        with mock.patch ("ldap.ldapobject.LDAPObject.modify_s", side_effect=expect):
            with self.assertRaises (LdapError) as received:
                self.con.modify ("dc=root", {}, {})
            
        self.assertEqual (str(expect), str(received.exception)) 

if __name__ == '__main__':
    unittest.main()
