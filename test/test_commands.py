import configuration
from ldapy.ldapy import Ldapy, NoSuchDN, AlreadyAtRoot
import unittest
import mock
from ldapy.commands import ChangeDN, List, PrintWorkingDN, Cat, Modify

def getLdapy ():
    con = configuration.getConnection ()
    return Ldapy (con)

class ChangeDNTests (unittest.TestCase):

    def test_successful_cd (self):
        with configuration.provision() as p:
            ldapy = getLdapy ()
            cmd = ChangeDN (ldapy)
            root = p.root
            cmd ([root])
            self.assertEqual (ldapy.cwd, root)

    def test_successful_cd_to_parent (self):
        with configuration.provision() as p:
            c = p.container()

            ldapy = getLdapy ()
            ldapy.changeDN (p.root)
            ldapy.changeDN (c.rdn)

            cmd = ChangeDN (ldapy)
            cmd ([".."])

            self.assertEqual (ldapy.cwd, c.parent)


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
        with configuration.provision() as p:
            ldapy = getLdapy ()
            ldapy.changeDN (p.root)

            cmd = ChangeDN (ldapy)

            nonexistent = "ou=Foobar"

            with mock.patch('sys.stdout.write') as print_mock:
                cmd ([nonexistent])

            msg = NoSuchDN._no_such_DN_in_parent % (nonexistent, p.root)
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
        with configuration.provision() as p:
            container = p.container()
            a = p.container(container)
            b = p.container(container)
            c = p.leaf(container)

            ldapy = getLdapy ()
            ldapy.changeDN (p.root)
            ldapy.changeDN (container.rdn)

            cmd = ChangeDN (ldapy)

            # Test return all on empty list
            matches = cmd.complete ([])
            self.assertListEqual (sorted([a.rdn, b.rdn, c.rdn]), sorted(matches))

            # Test several matches 
            matches = cmd.complete (["%s=" % a.dnComponent])
            self.assertItemsEqual (sorted([a.rdn, b.rdn]), sorted(matches))

            # Test unique match
            unique = b.rdn[:-1]
            matches = cmd.complete ([unique])
            self.assertListEqual ([b.rdn], matches)

    def test_usage (self):
        ldapy = getLdapy ()
        cmd = ChangeDN (ldapy)
        with mock.patch('sys.stdout.write') as print_mock:
            cmd.usage ([])

        msg = ChangeDN._usage % "cd"
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_syntax_error_calls_usage (self):
        ldapy = getLdapy ()
        cmd = ChangeDN (ldapy)
        cmd.usage = mock.create_autospec(cmd.usage)

        # Test calling with no parameters
        cmd ([])
        self.assertTrue(cmd.usage.called)
        cmd.usage.reset_mock ()

        # Test calling with too many parameters
        cmd (["a", "b"])
        self.assertTrue(cmd.usage.called)

class ListTests (unittest.TestCase):

    def getLdapyAtRoot (self):
        with configuration.provision() as p:
            ldapy = getLdapy ()
            ldapy.changeDN (p.root)
            return ldapy

    def test_successful_list (self):
        ldapy = self.getLdapyAtRoot()
        with configuration.provision() as p:
            c = p.container()
            ldapy.changeDN(c.rdn)

            l1 = p.leaf(c)
            l2 = p.leaf(c)

            cmd = List (ldapy)

            with mock.patch('sys.stdout.write') as print_mock:
                cmd ([])

            first_call = print_mock.call_args_list[0]
            args = first_call[0]
            first_arg = args[0]
            result = first_arg.split("\t")

            self.assertListEqual (sorted([l1.rdn, l2.rdn]), sorted(result))

    def test_usage (self):
        ldapy = self.getLdapyAtRoot()
        cmd = List (ldapy)
        with mock.patch('sys.stdout.write') as print_mock:
            cmd.usage ([])

        msg = List._usage % ("ls", ldapy.cwd)
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_syntax_error_calls_usage (self):
        cmd = List (self.getLdapyAtRoot())
        cmd.usage = mock.create_autospec(cmd.usage)

        # Test calling with too many parameters
        cmd (["a"])
        self.assertTrue(cmd.usage.called)

class PrintWorkingDNTests (unittest.TestCase):

    def getLdapyAtRoot (self):
        with configuration.provision() as p:
            ldapy = getLdapy ()
            ldapy.changeDN (p.root)
            return ldapy

    def test_successful_pwd (self):
        ldapy = self.getLdapyAtRoot()
        with configuration.provision() as p:
            c = p.container()
            ldapy.changeDN(c.rdn)

            cmd = PrintWorkingDN (ldapy)
            with mock.patch('sys.stdout.write') as print_mock:
                cmd ([])

            expect_calls = [mock.call(c.dn), mock.call("\n")]
            self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_usage (self):
        ldapy = self.getLdapyAtRoot()
        cmd = PrintWorkingDN (ldapy)
        with mock.patch('sys.stdout.write') as print_mock:
            cmd.usage ([])

        with configuration.provision() as p:
            c = p.container()
            ldapy.changeDN(c.rdn)

            msg = PrintWorkingDN._usage % ("pwd", p.root)
            expect_calls = [mock.call(msg), mock.call("\n")]
            self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_syntax_error_calls_usage (self):
        cmd = PrintWorkingDN (self.getLdapyAtRoot())
        cmd.usage = mock.create_autospec(cmd.usage)

        # Test calling with too many parameters
        cmd (["a"])
        self.assertTrue(cmd.usage.called)

class CatTests (unittest.TestCase):

    def getLdapyAtRoot (self):
        with configuration.provision() as p:
            ldapy = getLdapy ()
            self.root = p.root
            ldapy.changeDN (self.root)
            return ldapy

    def test_cat_self (self):
        cmd = Cat (self.getLdapyAtRoot())
        with mock.patch('sys.stdout.write') as print_mock:
            cmd (["."])

        wanted_call = mock.call ("objectClass: top")
        self.assertIn (wanted_call, print_mock.call_args_list)

    def test_cat_child (self):
        ldapy = self.getLdapyAtRoot()
        with configuration.provision() as p:
            l = p.leaf()

            cmd = Cat (ldapy)
            with mock.patch('sys.stdout.write') as print_mock:
                cmd ([l.rdn])

            wanted_call = mock.call ("%s: %s" % (l.dnComponent, l.name))
            self.assertIn (wanted_call, print_mock.call_args_list)

    def test_cat_superroot (self):
        cmd = Cat (self.getLdapyAtRoot())

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
        cmd = Cat (self.getLdapyAtRoot())

        nonexistent = "ou=Foobar"

        with mock.patch('sys.stdout.write') as print_mock:
            cmd ([nonexistent])

        msg = NoSuchDN._no_such_DN_in_parent % (nonexistent, self.root)
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_cat_completer (self):
        ldapy = self.getLdapyAtRoot()
        with configuration.provision() as p:
            container = p.container()
            ldapy.changeDN (container.rdn)

            a = p.container(container)
            b = p.container(container)
            c = p.leaf(container)

            cmd = Cat (ldapy)

            # Test return all on empty list
            matches = cmd.complete ([])
            self.assertListEqual (sorted([a.rdn, b.rdn, c.rdn]), sorted(matches))

            # Test several matches 
            matches = cmd.complete (["%s=" % a.dnComponent])
            self.assertItemsEqual (sorted([a.rdn, b.rdn]), sorted(matches))

            # Test unique match
            unique = b.rdn[:-1]
            matches = cmd.complete ([unique])
            self.assertListEqual ([b.rdn], matches)

    def test_usage (self):
        cmd = Cat (self.getLdapyAtRoot())
        with mock.patch('sys.stdout.write') as print_mock:
            cmd.usage ([])

        msg = Cat._usage % "cat"
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_syntax_error_calls_usage (self):
        ldapy = getLdapy ()
        cmd = Cat (ldapy)
        cmd.usage = mock.create_autospec(cmd.usage)

        # Test calling with no parameters
        cmd ([])
        self.assertTrue(cmd.usage.called)
        cmd.usage.reset_mock ()

        # Test calling with too many parameters
        cmd (["a", "b"])
        self.assertTrue(cmd.usage.called)

class ModifyTests (unittest.TestCase):
    def setUp (self):
        self.subcommands = [("add", "ldapy.commands.Modify.add"),
                ("delete", "ldapy.commands.Modify.delete"),
                ("replace", "ldapy.commands.Modify.replace")]

    def getLdapyAtRoot (self):
        with configuration.provision() as p:
            ldapy = getLdapy ()
            self.root = p.root
            ldapy.changeDN (self.root)
            return ldapy

    def test_usage (self):
        cmd = Modify (self.getLdapyAtRoot())
        with mock.patch('sys.stdout.write') as print_mock:
            cmd.usage ([])

        msg = Modify._usage % "modify"
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_subcommands_are_called (self):
        rdn = "cn=Relative"
        args = ["a", "b", "c"]
        cmd = Modify (self.getLdapyAtRoot())

        for name, fcn in self.subcommands:
            with mock.patch(fcn) as commandMock:
                cmd([rdn, name] + args)
                commandMock.assert_called_with (rdn, args)

    def test_unknown_subcommand_print_error_calls_usage (self):
        nonexistent = "non_existent_command"
        cmd = Modify (self.getLdapyAtRoot())
        cmd.usage = mock.create_autospec(cmd.usage)
        with mock.patch('sys.stdout.write') as print_mock:
            cmd(["RDN", nonexistent])

        msg = Modify._unknown_subcommand % nonexistent
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)
        
        self.assertTrue (cmd.usage.called)

    def test_call_with_no_arguments_prints_error_calls_usage (self):
        cmd = Modify (self.getLdapyAtRoot())
        cmd.usage = mock.create_autospec(cmd.usage)
        with mock.patch('sys.stdout.write') as print_mock:
            cmd([])

        msg = Modify._too_few_arguments % cmd.name
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)
        
        self.assertTrue (cmd.usage.called)

    def test_call_with_only_one_argument_prints_error_calls_usage (self):
        cmd = Modify (self.getLdapyAtRoot())
        cmd.usage = mock.create_autospec(cmd.usage)
        with mock.patch('sys.stdout.write') as print_mock:
            cmd(["RDN"])

        msg = Modify._too_few_arguments % cmd.name
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)
        
        self.assertTrue (cmd.usage.called)

    def test_call_sudcommands_with_wrong_number_of_parameters (self):
        tooFew = []
        tooMany = ["a", "b", "c", "d"]

        for name, fcn in self.subcommands:
            # Call with too few arguments
            cmd = Modify (self.getLdapyAtRoot())
            cmd.usage = mock.create_autospec(cmd.usage)

            with mock.patch('sys.stdout.write') as print_mock:
                cmd(["RDN", name] + tooFew)

            msg = Modify._wrong_number_of_arguments_to_subcommand % (cmd.name, name)
            expect_calls = [mock.call(msg), mock.call("\n")]
            self.assertListEqual (print_mock.call_args_list, expect_calls)
            self.assertTrue (cmd.usage.called)

        for name, fcn in self.subcommands:
            # Call with too many arguments
            cmd = Modify (self.getLdapyAtRoot())
            cmd.usage = mock.create_autospec(cmd.usage)

            with mock.patch('sys.stdout.write') as print_mock:
                cmd(["RDN", name] + tooMany)

            msg = Modify._wrong_number_of_arguments_to_subcommand % (cmd.name, name)
            expect_calls = [mock.call(msg), mock.call("\n")]
            self.assertListEqual (print_mock.call_args_list, expect_calls)
            self.assertTrue (cmd.usage.called)

    def test_add_calls_setAttribute (self):
        with configuration.provision() as p:
            attribute = "description"
            newValue = "test_add_calls_setAttribute"
            l = p.leaf()

            ldapy = self.getLdapyAtRoot()
            ldapy.setAttribute = mock.create_autospec (ldapy.setAttribute)

            cmd = Modify (ldapy)
            cmd([l.rdn, "add", attribute, newValue])

            ldapy.setAttribute.assert_called_with (l.rdn, attribute,
                    newValue = newValue, oldValue = None)

    def test_delete_calls_setAttribute (self):
        with configuration.provision() as p:
            attribute = "description"
            removeValue = "test_delete_calls_setAttribute"
            l = p.leaf()

            ldapy = self.getLdapyAtRoot()
            ldapy.setAttribute = mock.create_autospec (ldapy.setAttribute)

            cmd = Modify (ldapy)
            cmd([l.rdn, "delete", attribute, removeValue])

            ldapy.setAttribute.assert_called_with (l.rdn, attribute,
                    newValue = None, oldValue = removeValue)
        
    def test_replace_calls_setAttribute (self):
        with configuration.provision() as p:
            attribute = "description"
            newValue = "test_replace_calls_setAttribute_new"
            oldValue = "test_replace_calls_setAttribute_old"
            
            l = p.leaf()

            ldapy = self.getLdapyAtRoot()
            ldapy.setAttribute = mock.create_autospec (ldapy.setAttribute)

            cmd = Modify (ldapy)
            cmd([l.rdn, "replace", attribute, oldValue, newValue])

            ldapy.setAttribute.assert_called_with (l.rdn, attribute,
                    newValue = newValue, oldValue = oldValue)

    def test_call_add_with_nonexistent_DN (self):
        nonexistent = "dc=nonexistent"
        cmd = Modify (self.getLdapyAtRoot())

        with mock.patch('sys.stdout.write') as print_mock:
            cmd([nonexistent, "add", "should_not_need_this", "foobar"])

        msg = NoSuchDN._no_such_DN_in_parent % (nonexistent, self.root)
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_call_delete_with_nonexistent_DN (self):
        nonexistent = "dc=nonexistent"
        cmd = Modify (self.getLdapyAtRoot())

        with mock.patch('sys.stdout.write') as print_mock:
            cmd([nonexistent, "delete", "should_not_need_this", "foobar"])

        msg = NoSuchDN._no_such_DN_in_parent % (nonexistent, self.root)
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_call_replace_with_nonexistent_DN (self):
        nonexistent = "dc=nonexistent"
        cmd = Modify (self.getLdapyAtRoot())

        with mock.patch('sys.stdout.write') as print_mock:
            cmd([nonexistent, "replace", "should_not_need_this", "foo", "bar"])

        msg = NoSuchDN._no_such_DN_in_parent % (nonexistent, self.root)
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)
