import configuration
from ldapy.ldapy import Ldapy, NoSuchDN, AlreadyAtRoot
import unittest
import mock
from ldapy.commands import ChangeDN, List, PrintWorkingDN, Cat

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

    def test_cd_completer (self):
        ldapy = getLdapy ()
        cmd = ChangeDN (ldapy)
        root = "dc=nodomain"

        # Test return all on empty list
        matches = cmd.complete ([])
        self.assertListEqual ([root], matches)

        # Test several matches 
        ldapy.changeDN (root)
        children = ["ou=Groups","ou=People"]
        matches = cmd.complete (["ou="])
        self.assertItemsEqual (children, matches)

        # Test unique match
        matches = cmd.complete (["ou=P"])
        child = ["ou=People"]
        self.assertListEqual (child, matches)

    def test_usage (self):
        ldapy = getLdapy ()
        cmd = ChangeDN (ldapy)
        with mock.patch('sys.stdout.write') as print_mock:
            cmd.usage ([])

        msg = ChangeDN._usage % "cd"
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

        first_call = print_mock.call_args_list[0]
        args = first_call[0]
        first_arg = args[0]
        result = first_arg.split("\t")

        self.assertIn ("ou=Groups", result)
        self.assertIn ("ou=People", result)

    def test_usage (self):
        cmd = List (self.ldapy)
        with mock.patch('sys.stdout.write') as print_mock:
            cmd.usage ([])

        msg = List._usage % ("ls", self.ldapy.cwd)
        expect_calls = [mock.call(msg), mock.call("\n")]
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

    def test_usage (self):
        cmd = PrintWorkingDN (self.ldapy)
        with mock.patch('sys.stdout.write') as print_mock:
            cmd.usage ([])

        msg = PrintWorkingDN._usage % ("pwd", self.ldapy.cwd)
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

class CatTests (unittest.TestCase):

    def setUp (self):
        self.ldapy = getLdapy ()
        self.root = "dc=nodomain"
        self.ldapy.changeDN (self.root)

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

    def test_cat_superroot (self):
        cmd = Cat (self.ldapy)

        with mock.patch('sys.stdout.write') as print_mock:
            cmd ([".."])

        self.assertListEqual (print_mock.call_args_list, [])

    def test_unsuccessful_cat_parent_of_superroot (self):
        ldapy = getLdapy ()
        cmd = Cat (ldapy)

        with mock.patch('sys.stdout.write') as print_mock:
            cmd ([".."])

        msg = AlreadyAtRoot._already_at_root
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_unsuccessful_cat_of_nonexistent_child (self):
        cmd = Cat (self.ldapy)

        nonexistent = "ou=Foobar"

        with mock.patch('sys.stdout.write') as print_mock:
            cmd ([nonexistent])

        msg = NoSuchDN._no_such_DN_in_parent % (nonexistent, self.root)
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_cat_completer (self):
        ldapy = getLdapy ()
        cmd = Cat (ldapy)
        root = "dc=nodomain"

        # Test return all on empty list
        matches = cmd.complete ([])
        self.assertListEqual ([root], matches)

        # Test several matches 
        ldapy.changeDN (root)
        children = ["ou=Groups","ou=People"]
        matches = cmd.complete (["ou="])
        self.assertItemsEqual (children, matches)

        # Test unique match
        matches = cmd.complete (["ou=P"])
        child = ["ou=People"]
        self.assertListEqual (child, matches)

    def test_usage (self):
        cmd = Cat (self.ldapy)
        with mock.patch('sys.stdout.write') as print_mock:
            cmd.usage ([])

        msg = Cat._usage % "cat"
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

