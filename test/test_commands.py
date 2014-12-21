import configuration
import ldapy
import unittest
import mock
from commands import ChangeDN, List, PrintWorkingDN

def getLdapy ():
    con = configuration.getConnection ()
    return ldapy.Ldapy (con)

class ChangeDNTests (unittest.TestCase):

    def setUp (self):
        self.ldapy = getLdapy ()

    def test_successful_cd (self):
        cmd = ChangeDN (self.ldapy)
        cmd (["dc=nodomain"])
        self.assertEqual (self.ldapy.cwd, "dc=nodomain")

class ListTests (unittest.TestCase):

    def setUp (self):
        self.ldapy = getLdapy ()
        self.ldapy.changeDN ("dc=nodomain")

    def test_successful_list (self):
        cmd = List (self.ldapy)

        with mock.patch('sys.stdout.write') as print_mock:
            cmd ([])

        expect_calls = [mock.call("ou=Groups\tou=People"), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

class PrintWorkingDNTests (unittest.TestCase):

    def setUp (self):
        self.ldapy = getLdapy ()
        self.ldapy.changeDN ("dc=nodomain")
        self.ldapy.changeDN ("ou=People")

    def test_successful_pwd (self):
        cmd = PrintWorkingDN (self.ldapy)
        with mock.patch('sys.stdout.write') as print_mock:
            cmd ([])

        expect_calls = [mock.call("ou=People,dc=nodomain"), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)
        


