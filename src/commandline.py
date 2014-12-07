import readline
import shlex

class Command:
    def __init__ (self, command, options = []):
        self.command = command
        self.options = options

    def __call__ (self):
        pass

class NoSuchCommand (Exception):
    pass

class Commandline:
    def __init__ (self, commands, prompt = "$"):
        self.commands = {}
        for cmd in commands:
            self.commands[cmd.command] = cmd

    def parse_and_dispatch (self, line):
        words = shlex.split (line)
        if not words:
            return False
        try:
            cmd = self.commands[words[0]]
        except KeyError:
            raise NoSuchCommand ()





