#!/usr/bin/python

import unittest2
import mock
import pexpect
import os
import sys
import syslog
from ldapy.commandline import Commandline, Command, NoSuchCommand, ExitCommand

class Parser (unittest2.TestCase):

    def test_empty_line (self):
        cli = Commandline ([])

        assert not cli.parse_and_dispatch ("")

    def test_no_such_command (self):
        cli = Commandline ([])

        with self.assertRaises (NoSuchCommand):
            cli.parse_and_dispatch ("no_such_command")

    def test_dispatch (self):
        cmd1 = Command ("cmd1")
        cmd1.__call__ = mock.MagicMock()

        cmd2 = Command ("cmd2")
        cmd2.__call__ = mock.MagicMock()

        cli = Commandline ([cmd1, cmd2])

        cli.parse_and_dispatch ("cmd1")
        assert cmd1.__call__.called
        assert not cmd2.__call__.called

        cmd1.__call__.reset_mock ()
        cmd2.__call__.reset_mock ()

        cli.parse_and_dispatch ("cmd2")
        assert not cmd1.__call__.called
        assert cmd2.__call__.called

    def test_arguments (self):
        cmd = Command ("cmd")
        cmd.__call__ = mock.create_autospec (cmd.__call__)

        cli = Commandline ([cmd])

        cmdline = "cmd a  b\t c"
        args = ["a", "b", "c"]

        cli.parse_and_dispatch (cmdline)
        cmd.__call__.assert_called_once_with (args)

    def test_quoted_arguments (self):
        cmd = Command ("cmd")
        cmd.__call__ = mock.create_autospec(cmd.__call__)

        cli = Commandline ([cmd])

        args =       ["a", "b\"c\\\" d\"", "'e\" f'g", "h"]
        parsedArgs = ["a", "bc\" d",     "e\" fg",   "h"]
        cmdline = "cmd %s" % " ".join(args)

        cli.parse_and_dispatch (cmdline)
        cmd.__call__.assert_called_once_with (parsedArgs)

    def test_help_option (self):
        cmd = Command ("cmd")
        cmd.usage = mock.MagicMock()
        cli = Commandline ([cmd])

        # Test short option
        cmdline = "cmd -h"
        args = ["-h"]

        cli.parse_and_dispatch (cmdline)
        cmd.usage.assert_called_with (args)
        cmd.usage.reset_mock ()

        # Test short option, in the middle of cmdline
        cmdline = "cmd a -h b"
        args = ["a", "-h", "b"]

        cli.parse_and_dispatch (cmdline)
        cmd.usage.assert_called_with (args)
        cmd.usage.reset_mock ()

        # Test long option
        cmdline = "cmd --help"
        args = ["--help"]

        cli.parse_and_dispatch (cmdline)
        cmd.usage.assert_called_with (args)
        cmd.usage.reset_mock ()

        # Test long option, in the middle of cmdline
        cmdline = "cmd a --help b"
        args = ["a", "--help", "b"]

        cli.parse_and_dispatch (cmdline)
        cmd.usage.assert_called_with (args)
        cmd.usage.reset_mock ()


class BasicFunctionality (unittest2.TestCase):

    def test_exit (self):
        cli = Commandline ([])

        with mock.patch('__builtin__.raw_input', return_value='exit'):
            cli.loop ()

    def test_quit (self):
        cli = Commandline ([])

        with mock.patch('__builtin__.raw_input', return_value='quit'):
            cli.loop ()

    def test_exit_help (self):
        cmd = ExitCommand()
        with mock.patch('sys.stdout.write') as print_mock:
            cmd.usage ([])

        msg = ExitCommand._usage % "exit"
        expect_calls = [mock.call(msg), mock.call("\n")]
        self.assertListEqual (print_mock.call_args_list, expect_calls)

    def test_eof (self):
        cli = Commandline ([])

        with mock.patch('__builtin__.raw_input', side_effect=EOFError):
            cli.loop ()

    def test_ctrl_c (self):
        cli = Commandline ([])

        with mock.patch('__builtin__.raw_input', side_effect=KeyboardInterrupt):
            cli.loop ()

    def test_ctrl_c_clears_cmdline_if_it_has_input (self):
        child = create_sut_process (TrivialCommandline, TrivialCommandline.sut_trivial_commandline)

        child.expect ("\$")
        child.send("foobar")
        child.sendintr ()
        child.expect ("\$")
        child.sendline ("exit")
        child.wait ()

        assert child.exitstatus == 0

    def test_no_such_command (self):
        cli = Commandline ([])

        no_such_command = "no_such_command"

        inputs = [no_such_command, "quit"]

        with mock.patch('__builtin__.raw_input', side_effect=inputs):
            with mock.patch('sys.stdout.write') as print_mock:
                cli.loop ()

        expect_calls = \
                [mock.call(Commandline._no_such_command % no_such_command),\
                 mock.call("\n")]
        assert print_mock.call_args_list == expect_calls

    def test_command_raises_unexpected_exception (self):
        name = "cmd"
        error = "Foobar"

        cmd = Command (name)
        cmd.__call__ = mock.MagicMock (side_effect=Exception(error))

        cli = Commandline ([cmd])

        inputs = [name, "quit"]
        with mock.patch('__builtin__.raw_input', side_effect=inputs):
            with mock.patch('sys.stdout.write') as print_mock:
                cli.loop ()

        expect_calls = [mock.call(error), mock.call("\n")]
        assert print_mock.call_args_list == expect_calls

def create_sut_process (cls, method):
    pwd = os.path.dirname (__file__)
    script = os.path.join (pwd, "dispatch.py")
    args = ["coverage", "run", "-p", "--source", os.environ["NOSE_COVER_PACKAGE"], script, __name__, cls.__name__, method.__name__]
    cmdline = " ".join (args)
    print "Running:", cmdline
    return pexpect.spawn (" ".join (args), env = {"PYTHONPATH" : ":".join(sys.path)})

class TrivialCommandline:
    @staticmethod
    def sut_trivial_commandline (args):
        cli = Commandline ([])
        cli.loop ()

class Completer (unittest2.TestCase):

    def test_completer_called (self):
        child = create_sut_process (Completer, Completer.sut_completer_called)

        child.expect ("\$")
        child.send("\t")
        child.sendline ("quit")
        child.wait ()

        assert child.exitstatus == 0

    def test_unique_completion (self):
        child = create_sut_process (TrivialCommandline, TrivialCommandline.sut_trivial_commandline)

        child.expect ("\$")
        child.send("qui\t\n")
        child.wait ()

        assert child.exitstatus == 0

    def test_survives_completion_after_bogus_command (self):
        child = create_sut_process (TrivialCommandline, TrivialCommandline.sut_trivial_commandline)

        child.expect ("\$")
        child.send("foobar \t\n")
        child.send("exit\n")
        child.wait ()

        assert child.exitstatus == 0



    @staticmethod
    def sut_completer_called (args):
        with mock.patch ("ldapy.commandline.Commandline.complete") as completer:
            cli = Commandline ([])
            cli.loop ()

        assert completer.called

    @staticmethod
    def sut_trivial_commandline (args):
        cli = Commandline ([])
        cli.loop ()


    def test_list_when_ambiguous (self):
        child = create_sut_process (Completer, Completer.sut_list_when_ambiguous)

        child.expect ("\$")
        child.send("cmd\t\t")
        child.expect ("cmd1\s+cmd2")
        child.send("1\n")
        child.sendline ("quit")
        child.wait ()

        assert child.exitstatus == 0

    @staticmethod
    def sut_list_when_ambiguous (args):
        cmd1 = Command ("cmd1")
        cmd1.__call__ = mock.MagicMock()
        cmd2 = Command ("cmd2")
        cmd2.__call__ = mock.MagicMock()

        cli = Commandline ([cmd1, cmd2])
        cli.loop ()

        assert cmd1.__call__.called
        assert not cmd2.__call__.called

    def test_list_all_when_no_text (self):
        child = create_sut_process (TrivialCommandline, TrivialCommandline.sut_trivial_commandline)

        child.expect ("\$")
        child.send("\t\t")
        child.expect ("exit\s+quit")
        child.sendline ("quit")
        child.wait ()

        assert child.exitstatus == 0

    def test_commands_own_completer_is_called (self):
        child = create_sut_process (Completer, Completer.sut_commands_own_completer_is_called)

        child.expect ("\$")
        child.send("cmd \t\n")
        child.send("cmd a b\t\n")
        child.sendline ("quit")
        child.wait ()
        assert child.exitstatus == 0

    @staticmethod
    def sut_commands_own_completer_is_called (self):
        cmd = Command ("cmd")
        cmd.complete = mock.MagicMock ()

        cli = Commandline ([cmd])
        cli.loop ()

        calls = [mock.call([]), mock.call(["a", "b"])]
        assert cmd.complete.call_args_list == calls




