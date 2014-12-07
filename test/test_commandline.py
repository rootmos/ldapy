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

