from connection import Connection, ConnectionError
import unittest
import ldap
import ldap.ldapobject

class BasicConnection(unittest.TestCase):

    def setUp (self):
        self.uri = "ldap://localhost"
        self.con = Connection (self.uri)

        self.user = "cn=admin,dc=nodomain"
        self.password = "foobar"

    def test_initialization (self):
        self.assertEqual (self.con.uri, self.uri)
        self.assertIsInstance (self.con.con, ldap.ldapobject.LDAPObject)
        self.assertFalse (self.con.connected)

    def test_bind (self):
        self.con.bind (self.user, self.password)
        self.assertTrue (self.con.connected)

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
        uri = "ldap://localhost"
        bad_user ="cn=badguy,dc=nodomain"
        bad_password ="urg"
        con = Connection (uri)
        with self.assertRaises(ConnectionError) as received:
            con.bind (bad_user, bad_password)

        msg = Connection._bad_auth_error_msg % bad_user
        expected = ConnectionError (con, msg)
        self.assertEqual (str(received.exception), str(expected))


if __name__ == '__main__':
    unittest.main()
