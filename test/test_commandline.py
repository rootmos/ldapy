#!/usr/bin/python

import unittest
import mock
import pexpect
import os
import sys
from commandline import Commandline, Command, NoSuchCommand

class Parser (unittest.TestCase):

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
        cmd.__call__ = mock.MagicMock()

        cli = Commandline ([cmd])

        cmdline = "cmd a \"b c\""
        args = ["a", "b c"]

        cli.parse_and_dispatch (cmdline)

        cmd.__call__.assert_called_with (args)


class BasicFunctionality (unittest.TestCase):

    def test_exit (self):
        cli = Commandline ([])

        with mock.patch('__builtin__.raw_input', return_value='exit'):
            cli.loop ()

    def test_quit (self):
        cli = Commandline ([])

        with mock.patch('__builtin__.raw_input', return_value='quit'):
            cli.loop ()

    def test_eof (self):
        cli = Commandline ([])

        with mock.patch('__builtin__.raw_input', side_effect=EOFError):
            cli.loop ()

    def test_no_such_command (self):
        cli = Commandline ([])

        no_such_command = "no_such_command"

        inputs = [no_such_command, "quit"]

        with mock.patch('__builtin__.raw_input', side_effect=inputs),\
                mock.patch('sys.stdout.write') as print_mock:
                    cli.loop ()

        expect_calls = \
                [mock.call(Commandline._no_such_command % no_such_command),\
                 mock.call("\n")]
        assert print_mock.call_args_list == expect_calls

class Completer (unittest.TestCase):

    def test_completer_called (self):
        pwd = os.path.dirname (__file__)
        script = os.path.join (pwd, "dispatch.py")
        args = [script, __name__, Completer.__name__, Completer.sut_completer_called.__name__]

        child = pexpect.spawn (" ".join (args), env = {"PYTHONPATH" : ":".join(sys.path)})

        child.expect ("$")
        child.send("\t")
        child.sendline ("quit")
        child.close ()

        print sys.path
        assert child.exitstatus == 0

    @staticmethod
    def sut_completer_called (args):
        with mock.patch ("commandline.Commandline.complete") as completer:
            cli = Commandline ([])
            cli.loop ()

        assert completer.called

