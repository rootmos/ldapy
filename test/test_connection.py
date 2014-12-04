import connection
import unittest

class BasicConnection(unittest.TestCase):

    def setUp (self):
        self.con = connection.Connection ("ldap://localhost")

    def test_connected (self):
        self.assertTrue (self.con.connected)

if __name__ == '__main__':
    unittest.main()
