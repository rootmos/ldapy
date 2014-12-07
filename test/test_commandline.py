import unittest
import mock
from commandline import Commandline, Command, NoSuchCommand

class Parser (unittest.TestCase):

    def test_empty_line (self):
        cli = Commandline ([])

        assert not cli.parse_and_dispatch ("")

    def test_no_such_command (self):
        cmd = Command ("cmd")
        cmd.__call__ = mock.MagicMock()

        cli = Commandline ([cmd])

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

