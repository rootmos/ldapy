# This file is part of ldapy.
#
# ldapy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ldapy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ldapy.  If not, see <http://www.gnu.org/licenses/>.

import readline
import shlex
import sys

class Command:
    def __init__ (self, command, options = []):
        self.command = command
        self.options = options

    _syntax_error = "Syntax error!"

    def syntaxError (self, reason, args):
        print Command._syntax_error, reason
        self.usage (args)

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
        self.name = "exit"
        Command.__init__ (self, self.name)

    def __call__ (self, args):
        raise ExitCommandline

    _usage = """Usage: %s
Exit ldapy."""

    def usage (self, words):
        print ExitCommand._usage % self.name

class Commandline:
    def __init__ (self, commands, prompt = "$ "):
        self.prompt = prompt
        readline.parse_and_bind('tab: complete')
        readline.set_completer (self.complete)
        readline.set_completer_delims (" \t")
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
            if ("-h" in words) or ("--help" in words):
                return cmd.usage (words)
            else:
                return cmd (words)
        except KeyError:
            raise NoSuchCommand (cmd_name)

    _no_such_command = "No such command: %s"

    def loop (self):
        while True:
           try:
               line = raw_input (self.prompt)
               self.parse_and_dispatch (line)
           except NoSuchCommand as e:
               print e
           except KeyboardInterrupt:
               sys.stdout.write ("\n")
               if not readline.get_line_buffer():
                   return
           except EOFError:
               return
           except ExitCommandline:
               return
           except Exception as e:
               print e

    def complete (self, text, state):
        # Check if it's the first time we are getting a call for this text,
        # and if so we populate the list of matches
        if state == 0:
            line = readline.get_line_buffer()

            # Check if there's any text or there's stuff in the buffer
            if text or line:
                # If the text contains more than a word then we delegate to that
                # commands completer to populate the matches
                # (And if the string ends with a space, then surely we have more than a word.)
                words = shlex.split (line)
                if len(words) > 1 or (len(words)==1 and (line.endswith(" ") or line.endswith("\t"))):
                    cmd_name = words.pop (0)
                    try:
                        cmd = self.commands[cmd_name]
                        self.matches = cmd.complete (words)
                    except KeyError:
                        return None
                else:
                    # We are completing in the first word
                    self.matches = []
                    for cmd in self.commands.keys():
                        if cmd.startswith (text):
                            self.matches.append (cmd)
            else:
                # If there's none, we populate the matches with the commands' names
                self.matches = self.commands.keys()

            self.matches.sort ()

        if state < len (self.matches):
            return self.matches[state]
        else:
            return None

