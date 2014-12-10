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
    def __init__ (self, cmd):
        self.cmd = cmd


    def __str__ (self):
        return Commandline._no_such_command % self.cmd


class ExitCommandline (Exception):
    pass

class ExitCommand (Command):
    def __init__ (self):
        Command.__init__ (self, "exit")

    def __call__ (self, args):
        raise ExitCommandline

import syslog

class Commandline:
    def __init__ (self, commands, prompt = "$ "):
        self.prompt = prompt
        readline.parse_and_bind('tab: complete')
        readline.set_completer (self.complete)
        self.commands = { "exit" : ExitCommand(), "quit" : ExitCommand() }
        for cmd in commands:
            self.commands[cmd.command] = cmd

    def parse_and_dispatch (self, line):
        words = shlex.split (line)
        if not words:
            return False

        cmd_name = words.pop (0)
        try:
            cmd = self.commands[cmd_name]
            return cmd (words)
        except KeyError:
            raise NoSuchCommand (cmd_name)

    _no_such_command = "No such command: %s"

    def loop (self):
        try:
            while True:
                line = raw_input (self.prompt)
                try:
                    self.parse_and_dispatch (line)
                except NoSuchCommand as e:
                    print e
        except EOFError:
            return
        except ExitCommandline:
            return

    def complete (self, text, state):
        if text:
            self.matches = []
            for cmd in self.commands.keys():
                if cmd.startswith (text):
                    self.matches.append (cmd)

        if state < len (self.matches):
            return self.matches[state]
        else:
            return None

