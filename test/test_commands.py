import configuration
from ldapy import Ldapy, NoSuchDN, AlreadyAtRoot
import unittest
import mock
from commands import ChangeDN, List, PrintWorkingDN, Cat

def getLdapy ():
    con = configuration.getConnection ()
    return Ldapy (con)

class ChangeDNTests (unittest.TestCase):

    def test_successful_cd (self):
        ldapy = getLdapy ()
        cmd = ChangeDN (ldapy)
        root = "dc=nodomain"
        cmd ([root])
        self.assertEqual (ldapy.cwd, root)

    def test_successful_cd_to_parent (self):
        ldapy = getLdapy ()
        root = "dc=nodomain"
        child = "ou=People"
        ldapy.changeDN (root)
        ldapy.changeDN (child)

        cmd = ChangeDN (ldapy)
        cmd ([".."])

        self.assertEqual (ldapy.cwd, root)


    def test_unsuccessful_cd_to_root (self):
        ldapy = getLdapy ()
        cmd = ChangeDN (ldapy)

        nonexistent = "dc=nonexistent"

        with mock.patch('sys.stdout.write') as print_mock:
            cmd ([nonexistent])

        msg = NoSuchDN._no_such_DN_in_root % nonexistent
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_unsuccessful_cd_to_child (self):
        ldapy = getLdapy ()
        root = "dc=nodomain"
        ldapy.changeDN (root)

        cmd = ChangeDN (ldapy)

        nonexistent = "ou=Foobar"

        with mock.patch('sys.stdout.write') as print_mock:
            cmd ([nonexistent])

        msg = NoSuchDN._no_such_DN_in_parent % (nonexistent, root)
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_unsuccessful_cd_one_level_too_far (self):
        ldapy = getLdapy ()

        cmd = ChangeDN (ldapy)

        with mock.patch('sys.stdout.write') as print_mock:
            cmd ([".."])

        msg = AlreadyAtRoot._already_at_root
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)


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

class CatTests (unittest.TestCase):

    def setUp (self):
        self.ldapy = getLdapy ()
        self.ldapy.changeDN ("dc=nodomain")

    def test_cat_self (self):
        cmd = Cat (self.ldapy)
        with mock.patch('sys.stdout.write') as print_mock:
            cmd (["."])

        wanted_call = mock.call ("objectClass: top")
        self.assertIn (wanted_call, print_mock.call_args_list)

    def test_cat_child (self):
        cmd = Cat (self.ldapy)
        with mock.patch('sys.stdout.write') as print_mock:
            cmd (["ou=People"])

        wanted_call = mock.call ("objectClass: organizationalUnit")
        self.assertIn (wanted_call, print_mock.call_args_list)
