from ldapy.connection import Connection, ConnectionError, LdapError, scopeBase
import unittest
import mock
import ldap
import ldap.ldapobject
import ldap.modlist
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

class Operations (unittest.TestCase):
    def setUp (self):
        self.con = Connection (configuration.uri)
        self.con.bind (configuration.admin, configuration.admin_password)
        assert self.con.connected

    def test_search_delegates (self):
        dn = "cn=Foobar"
        scope = scopeBase
        ldapScope = ldap.SCOPE_BASE
        attrlist = ["a", "b"]
        with mock.patch ("ldap.ldapobject.LDAPObject.search_s", autospec=True) as search_mock:
            self.con.search (dn, scope, attrlist = attrlist)

        search_mock.assert_called_once_with(self.con._ldap, dn, ldapScope, attrlist = attrlist)

    def test_search_passes_on_ldap_errors (self):
        expect = ldap.OTHER("Foobar")
        with mock.patch ("ldap.ldapobject.LDAPObject.search_s", side_effect=expect):
            with self.assertRaises (LdapError) as received:
                self.con.search ("dc=root", scopeBase)

        self.assertEqual (str(expect), str(received.exception))

    def test_modify_delegates (self):
        dn = "cn=Foobar"
        oldAttrs = {"foo": "bar"}
        newAttrs = {"foo": "baz"}
        with mock.patch ("ldap.ldapobject.LDAPObject.modify_s", autospec=True) as modify_mock:
            self.con.modify (dn, oldAttrs, newAttrs)

        ldif = ldap.modlist.modifyModlist (oldAttrs, newAttrs)
        modify_mock.assert_called_once_with (self.con._ldap, dn, ldif)

    def test_modify_passes_on_ldap_errors (self):
        expect = ldap.OTHER("Foobar")
        with mock.patch ("ldap.ldapobject.LDAPObject.modify_s", side_effect=expect):
            with self.assertRaises (LdapError) as received:
                self.con.modify ("dc=root", {}, {})

        self.assertEqual (str(expect), str(received.exception))

    def test_delete_delegates (self):
        dn = "cn=Foobar"
        with mock.patch ("ldap.ldapobject.LDAPObject.delete_s", autospec=True) as delete_mock:
            self.con.delete (dn)

        delete_mock.assert_called_once_with (self.con._ldap, dn)

    def test_delete_passes_on_ldap_errors (self):
        expect = ldap.OTHER("Foobar")
        with mock.patch ("ldap.ldapobject.LDAPObject.delete_s", side_effect=expect):
            with self.assertRaises (LdapError) as received:
                self.con.delete ("dc=root")

        self.assertEqual (str(expect), str(received.exception))

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


if __name__ == '__main__':
    unittest.main()
