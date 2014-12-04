import connection
import unittest
import ldap
import ldap.ldapobject

class BasicConnection(unittest.TestCase):

    def setUp (self):
        self.uri = "ldap://localhost"
        self.con = connection.Connection (self.uri)

    def test_initialization (self):
        self.assertEqual (self.con.uri, self.uri)
        self.assertIsInstance (self.con.con, ldap.ldapobject.LDAPObject)
        self.assertFalse (self.con.connected)

    def test_connected (self):
        self.assertTrue (self.con.connected)


if __name__ == '__main__':
    unittest.main()
