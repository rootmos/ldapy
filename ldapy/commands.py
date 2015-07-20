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

from commandline import Command
from ldapy import Ldapy, AlreadyAtRoot
from exceptions import NoSuchObject, NoSuchObjectInRoot

class List (Command):
    def __init__ (self, ldapy):
        self.name = "ls"
        Command.__init__ (self, self.name)
        self.ldapy = ldapy

    _wrong_number_of_arguments = "%s must be called without arguments"
    def __call__ (self, args):
        # Check syntax
        if len(args) != 0:
            self.syntaxError (List._wrong_number_of_arguments % self.name, args)
            return

        print "\t".join (self.ldapy.children)

    _usage = """Usage: %s
Lists children of current DN (currently: %s)."""

    def usage (self, words):
        print List._usage % (self.name, self.ldapy.cwd)


class ChangeDN (Command):
    def __init__ (self, ldapy):
        self.name = "cd"
        Command.__init__ (self, self.name)
        self.ldapy = ldapy

    _wrong_number_of_arguments = "%s must be called with exactly one argument"

    def __call__ (self, args):
        # Check syntax
        if len(args) != 1:
            self.syntaxError (ChangeDN._wrong_number_of_arguments % self.name, args)
            return

        try:
            self.ldapy.changeDN (args[0])
        except AlreadyAtRoot as e:
            print e
        except NoSuchObject as e:
            print e
        except NoSuchObjectInRoot as e:
            print e

    def complete (self, words):
        if len(words):
            return self.ldapy.completeChild (words[0])
        else:
            return self.ldapy.children

    _usage = """Usage: %s relativeDN
Changes DN to a child DN specified by relativeDN."""

    def usage (self, words):
        print ChangeDN._usage % self.name

class PrintWorkingDN (Command):
    def __init__ (self, ldapy):
        self.name = "pwd"
        Command.__init__ (self, self.name)
        self.ldapy = ldapy

    _wrong_number_of_arguments = "%s must be called without arguments"
    def __call__ (self, args):
        # Check syntax
        if len(args) != 0:
            self.syntaxError (PrintWorkingDN._wrong_number_of_arguments % self.name, args)
            return

        print self.ldapy.cwd

    _usage = """Usage: %s
Prints current DN (which currently is: %s)."""

    def usage (self, words):
        print PrintWorkingDN._usage % (self.name, self.ldapy.cwd)

class Cat (Command):
    def __init__ (self, ldapy):
        self.name = "cat"
        Command.__init__ (self, self.name)
        self.ldapy = ldapy

    _wrong_number_of_arguments = "%s must be called with exactly one argument"
    def __call__ (self, args):
        # Check syntax
        if len(args) != 1:
            self.syntaxError (Cat._wrong_number_of_arguments % self.name, args)
            return

        try:
            attributes = self.ldapy.getAttributes (args[0])
            for attribute, value_list in attributes.items():
                for value in value_list:
                    print "%s: %s" % (attribute, value)
        except AlreadyAtRoot as e:
            print e
        except NoSuchObject as e:
            print e

    def complete (self, words):
        if len(words):
            return self.ldapy.completeChild (words[0])
        else:
            return self.ldapy.children

    _usage = """Usage: %s relativeDN
Prints the attributes of a DN specified by relativeDN."""

    def usage (self, words):
        print Cat._usage % self.name

class Modify (Command):
    def __init__ (self, ldapy):
        self.name = "modify"
        Command.__init__ (self, self.name)
        self.ldapy = ldapy

    def __call__ (self, args):
        if len(args) < 2:
            print Modify._too_few_arguments % self.name
            self.usage(args)
            return 

        rdn = args[0]
        subcommand = args[1]
        subArgs = args[2:]

        if subcommand  == "add":
            self.add (rdn, subArgs)
        elif subcommand == "delete":
            self.delete (rdn, subArgs)
        elif subcommand == "replace":
            self.replace (rdn, subArgs)
        else:
            print Modify._unknown_subcommand % subcommand
            self.usage (args)
    
    def complete (self, words):
        # On the first word we complete by children
        if len(words) <= 1:
            if len(words) == 1:
                return self.ldapy.completeChild (words[0])
            else:
                return self.ldapy.children
        else:
            return []
    
    _too_few_arguments = "%s called with too few arguments"
    _wrong_number_of_arguments_to_subcommand = "%s %s was called with wrong number of parameters"
    _unknown_subcommand = "No such subcommand: %s"
    _usage = """Usage: %s relativeDN (add|delete|replace) ...
Modifies attribute in the object specified by the relativeDN.

Subcommands:
    add ATTRIBUTE VALUE       - adds VALUE to ATTRIBUTE
    delete ATTRIBUTE VALUE    - removes VALUE from ATTRIBUTE
    replace ATTRIBUTE OLD NEW - replaces OLD value with NEW value in ATTRIBUTE
"""

    def usage (self, words):
        print Modify._usage % self.name

    def add (self, rdn,  args):
        if len(args) != 2:
            print Modify._wrong_number_of_arguments_to_subcommand % (self.name, "add")
            self.usage (args)
            return

        attribute = args[0]
        newValue = args[1]

        try:
            self.ldapy.setAttribute (rdn, attribute,
                    newValue = newValue, oldValue = None)
        except NoSuchObject as e:
            print e

    def delete (self, rdn, args):
        if len(args) != 2:
            print Modify._wrong_number_of_arguments_to_subcommand % (self.name, "delete")
            self.usage (args)
            return

        attribute = args[0]
        oldValue = args[1]

        try:
            self.ldapy.setAttribute (rdn, attribute,
                    oldValue = oldValue, newValue = None)
        except NoSuchObject as e:
            print e

    def replace (self, rdn, args):
        if len(args) != 3:
            print Modify._wrong_number_of_arguments_to_subcommand % (self.name, "replace")
            self.usage (args)
            return

        attribute = args[0]
        oldValue = args[1]
        newValue = args[2]

        try:
            self.ldapy.setAttribute (rdn, attribute,
                    oldValue = oldValue, newValue = newValue)
        except NoSuchObject as e:
            print e

class Delete(Command):
    def __init__ (self, ldapy):
        self.name = "delete"
        Command.__init__ (self, self.name)
        self.ldapy = ldapy

    def __call__ (self, args):
        if len(args) != 1:
            print Delete._wrong_number_of_arguments % self.name
            self.usage (args)
            return

        relDN = args[0]
        try:
            self.ldapy.delete (relDN)
        except NoSuchObject as e:
            print e

    _wrong_number_of_arguments = "%s has to be called with only one argument."
    _usage = """Usage: %s relativeDN
Deletes the object specified by the relativeDN, if the object has children they
will be deleted recusively as well.
"""

    def usage (self, words):
        print Delete._usage % self.name

class Add(Command):
    def __init__ (self, ldapy):
        self.name = "add"
        Command.__init__ (self, self.name)
        self.ldapy = ldapy

    _usage = """Usage: %s relativeDN (attribute:value)+
Adds an object with relativeDN and attributes to the current object.
"""
    _wrong_number_of_arguments = "%s has to be called with at least two arguments."
    _malformed_attribute = "Malformed attribute: %s"

    def usage (self, words):
        print Add._usage % self.name

    def __call__ (self, args):
        if len(args) < 2:
            print Add._wrong_number_of_arguments % self.name
            self.usage(args)
            return

        rdn = args[0]
        attrs = {}
        for raw in args[1:]:
            pair = raw.split (":", 1)
            if len(pair) != 2:
                print Add._malformed_attribute % raw
                self.usage(args)
                return

            attr = pair[0]
            value = pair[1]
            attrs[attr] = value

        self.ldapy.add (rdn, attrs)
