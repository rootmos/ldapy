import readline
import shlex

class Command:
    def __init__ (self, command, options = []):
        self.command = command
        self.options = options

    def help (self):
        pass

    def __call__ (self, args):
        pass

class NoSuchCommand (Exception):
    pass

class ExitCommandline (Exception):
    pass

class ExitCommand (Command):
    def __init__ (self):
        Command.__init__ (self, "exit")

    def __call__ (self, args):
        raise ExitCommandline


class Commandline:
    def __init__ (self, commands, prompt = "$"):
        self.commands = { "exit" : ExitCommand(), "quit" : ExitCommand() }
        for cmd in commands:
            self.commands[cmd.command] = cmd

    def parse_and_dispatch (self, line):
        words = shlex.split (line)
        if not words:
            return False
        try:
            cmd_name = words.pop (0)
            cmd = self.commands[cmd_name]
            return cmd (words)
        except KeyError:
            raise NoSuchCommand ()

    def loop (self):
        try:
            while True:
                line = raw_input ()
                self.parse_and_dispatch (line)
        except EOFError:
            return
        except ExitCommandline:
            return







