import configuration
from ldapy.ldapy import Ldapy, AlreadyAtRoot
import unittest2
import mock
from ldapy.commands import ChangeDN, List, PrintWorkingDN, Cat, Modify, Delete, Add
from ldapy.exceptions import NoSuchObject, NoSuchObjectInRoot

def getLdapy ():
    con = configuration.getConnection ()
    return Ldapy (con)

def verifyRDNCompleterOnFirstArgument (test, commandType):
    with configuration.provision() as p:
        # Isolate ourselves in a container to be sure about the contents
        container = p.container()

        a = p.container(container)
        b = p.container(container)
        c = p.leaf(container)

        ldapy = getLdapy ()
        ldapy.changeDN (p.root)
        ldapy.changeDN (container.rdn)

        cmd = commandType (ldapy)

        # Test return all on empty list
        matches = cmd.complete ([])
        test.assertListEqual (sorted([a.rdn, b.rdn, c.rdn]), sorted(matches))

        # Test several matches 
        matches = cmd.complete (["%s=" % a.dnComponent])
        test.assertItemsEqual (sorted([a.rdn, b.rdn]), sorted(matches))

        # Test unique match
        unique = b.rdn[:-1]
        matches = cmd.complete ([unique])
        test.assertListEqual ([b.rdn], matches)
        
def verifyStopsCompletingAfter (test, commandType, n, m = 10):
    with configuration.provision() as p:
        container = p.container()

        ldapy = getLdapy ()
        ldapy.changeDN (p.root)
        ldapy.changeDN (container.rdn)

        l = p.leaf(container)
        cmd = commandType (ldapy)
        
        firstArgs = [l.rdn for i in range(1, n+1)]
        manyArgs = [l.rdn for i in range(n+1, m)]
        args = []
        for arg in manyArgs:
            args.append(arg)

            allArgs = firstArgs + args
            print "Calling cmd.complete with arguments: %s" % allArgs
            matches = cmd.complete (allArgs)
            test.assertListEqual(matches, [])


class ChangeDNTests (unittest2.TestCase):

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

        msg = NoSuchObjectInRoot._no_such_DN_in_root % nonexistent
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_unsuccessful_cd_to_child (self):
        with configuration.provision() as p:
            ldapy = getLdapy ()
            ldapy.changeDN (p.root)

            cmd = ChangeDN (ldapy)

            nonexistentRDN = "ou=Foobar"
            nonexistent = "%s,%s" % (nonexistentRDN, p.root)

            with mock.patch('sys.stdout.write') as print_mock:
                cmd ([nonexistentRDN])

            msg = NoSuchObject._dn_does_not_exist % nonexistent
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
        verifyRDNCompleterOnFirstArgument (self, ChangeDN)

    def test_no_completion_on_other_arguments (self):
        verifyStopsCompletingAfter (self, ChangeDN, 1)

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

class ListTests (unittest2.TestCase):

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

class PrintWorkingDNTests (unittest2.TestCase):

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

class CatTests (unittest2.TestCase):

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

        nonexistentRDN = "ou=Foobar"
        nonexistent = "%s,%s" % (nonexistentRDN, self.root)

        with mock.patch('sys.stdout.write') as print_mock:
            cmd ([nonexistentRDN])

        msg = NoSuchObject._dn_does_not_exist % nonexistent
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_unsuccessful_cat_of_malformed_DN (self):
        cmd = Cat (self.getLdapyAtRoot())

        malformedRDN = "Foobar"
        malformed = "%s,%s" % (malformedRDN, self.root)

        with mock.patch('sys.stdout.write') as print_mock:
            cmd ([malformedRDN])

        msg = NoSuchObject._dn_does_not_exist % malformed
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_cat_completer (self):
        verifyRDNCompleterOnFirstArgument (self, Cat)

    def test_no_completion_on_other_arguments (self):
        verifyStopsCompletingAfter (self, Cat, 1)

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

class ModifyTests (unittest2.TestCase):
    def setUp (self):
        self.subcommands = [("add", "ldapy.commands.Modify.add"),
                ("delete", "ldapy.commands.Modify.delete"),
                ("replace", "ldapy.commands.Modify.replace")]

        with configuration.provision() as p:
            self.root = p.root

    def getLdapyAtRoot (self):
        with configuration.provision() as p:
            ldapy = getLdapy ()
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
        nonexistentRDN = "dc=nonexistent"
        nonexistent = "%s,%s" % (nonexistentRDN, self.root)

        cmd = Modify (self.getLdapyAtRoot())

        with mock.patch('sys.stdout.write') as print_mock:
            cmd([nonexistentRDN, "add", "should_not_need_this", "foobar"])

        msg = NoSuchObject._dn_does_not_exist % nonexistent
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_call_delete_with_nonexistent_DN (self):
        nonexistentRDN = "dc=nonexistent"
        nonexistent = "%s,%s" % (nonexistentRDN, self.root)

        cmd = Modify (self.getLdapyAtRoot())

        with mock.patch('sys.stdout.write') as print_mock:
            cmd([nonexistentRDN, "delete", "should_not_need_this", "foobar"])

        msg = NoSuchObject._dn_does_not_exist % nonexistent
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_call_replace_with_nonexistent_DN (self):
        nonexistentRDN = "dc=nonexistent"
        nonexistent = "%s,%s" % (nonexistentRDN, self.root)

        cmd = Modify (self.getLdapyAtRoot())

        with mock.patch('sys.stdout.write') as print_mock:
            cmd([nonexistentRDN, "replace", "should_not_need_this", "foo", "bar"])

        msg = NoSuchObject._dn_does_not_exist % nonexistent
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_rdn_completer (self):
        verifyRDNCompleterOnFirstArgument (self, Modify)

    def test_no_completion_on_other_arguments (self):
        verifyStopsCompletingAfter (self, Modify, 1)


class DeleteTests (unittest2.TestCase):
    def getLdapyAtRoot (self):
        with configuration.provision() as p:
            ldapy = getLdapy ()
            self.root = p.root
            ldapy.changeDN (self.root)
            return ldapy

    def test_usage (self):
        cmd = Delete (self.getLdapyAtRoot())
        with mock.patch('sys.stdout.write') as print_mock:
            cmd.usage ([])

        msg = Delete._usage % "delete"
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_rdn_completer (self):
        verifyRDNCompleterOnFirstArgument (self, Delete)

    def test_no_completion_on_other_arguments (self):
        verifyStopsCompletingAfter (self, Delete, 1)

    def test_successful_delete_calls_ldapy_delete (self):
        ldapy = self.getLdapyAtRoot()
        cmd = Delete (ldapy)

        ldapy.delete = mock.create_autospec (ldapy.delete)
        relDN = "dc=Foobar"
        cmd([relDN])
        ldapy.delete.assert_called_once_with (relDN)

    def test_too_few_arguments_prints_error_calls_usage (self):
        cmd = Delete (self.getLdapyAtRoot())

        cmd.usage = mock.create_autospec(cmd.usage)
        args = []
        with mock.patch('sys.stdout.write') as print_mock:
            cmd(args)

        msg = Delete._wrong_number_of_arguments % cmd.name
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)
        
        cmd.usage.assert_called_once_with (args)

    def test_too_many_arguments_prints_error_calls_usage (self):
        cmd = Delete (self.getLdapyAtRoot())

        cmd.usage = mock.create_autospec(cmd.usage)
        args = ["a", "b"]
        with mock.patch('sys.stdout.write') as print_mock:
            cmd(args)

        msg = Delete._wrong_number_of_arguments % cmd.name
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)
        
        cmd.usage.assert_called_once_with (args)

    def test_non_existent_RDN (self):
        with configuration.provision() as p:
            nonexistentRDN = "dc=Foobar"
            nonexistent = "%s,%s" % (nonexistentRDN, p.root)

        cmd = Delete (self.getLdapyAtRoot())

        with mock.patch('sys.stdout.write') as print_mock:
            cmd ([nonexistentRDN])

        msg = NoSuchObject._dn_does_not_exist % nonexistent
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

class AddTests (unittest2.TestCase):
    def getLdapyAtRoot (self):
        with configuration.provision() as p:
            ldapy = getLdapy ()
            self.root = p.root
            ldapy.changeDN (self.root)
            return ldapy

    def test_usage (self):
        cmd = Add (self.getLdapyAtRoot())
        with mock.patch('sys.stdout.write') as print_mock:
            cmd.usage ([])

        msg = Add._usage % "add"
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_successful_add_calls_ldapy_add (self):
        ldapy = self.getLdapyAtRoot()
        cmd = Add (ldapy)

        ldapy.add = mock.create_autospec (ldapy.add)

        relDN = "dc=Foo"
        attrsDict = {"objectClass": "Bar", "dc": "Foo"}

        attrs = []
        for key, value in attrsDict.iteritems():
            attrs.append ("%s:%s" % (key, value))
        cmd([relDN] + attrs)

        ldapy.add.assert_called_once_with (relDN, attrsDict)

    def test_successful_add_calls_ldapy_add_with_tricky_name (self):
        ldapy = self.getLdapyAtRoot()
        cmd = Add (ldapy)

        ldapy.add = mock.create_autospec (ldapy.add)

        relDN = "dc=Foo"
        attrsDict = {"objectClass": "\"Bar Baz\"", "dc": "Tricky:Name"}

        attrs = []
        for key, value in attrsDict.iteritems():
            attrs.append ("%s:%s" % (key, value))
        cmd([relDN] + attrs)

        ldapy.add.assert_called_once_with (relDN, attrsDict)

    def test_too_few_arguments_prints_error_calls_usage (self):
        cmd = Add (self.getLdapyAtRoot())

        cmd.usage = mock.create_autospec(cmd.usage)
        args = []
        with mock.patch('sys.stdout.write') as print_mock:
            cmd(args)

        msg = Add._wrong_number_of_arguments % cmd.name
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

        cmd.usage.assert_called_once_with (args)

    def test_attribute_malformed_prints_error_calls_usage (self):
        cmd = Add (self.getLdapyAtRoot())

        cmd.usage = mock.create_autospec(cmd.usage)
        malformed = "malformed"
        args = ["dc=Foo", "a:b", malformed, "c:d"]
        with mock.patch('sys.stdout.write') as print_mock:
            cmd(args)

        msg = Add._malformed_attribute % malformed
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

        cmd.usage.assert_called_once_with (args)

