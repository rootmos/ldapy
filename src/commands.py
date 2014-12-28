
from commandline import Command
from ldapy import Ldapy, NoSuchDN, AlreadyAtRoot

class List (Command):
    def __init__ (self, ldapy):
        self.name = "ls"
        Command.__init__ (self, self.name)
        self.ldapy = ldapy

    def __call__ (self, args):
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

    def __call__ (self, args):
        try:
            self.ldapy.changeDN (args[0])
        except AlreadyAtRoot as e:
            print e
        except NoSuchDN as e:
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

    def __call__ (self, args):
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

    def __call__ (self, args):
        try:
            attributes = self.ldapy.getAttributes (args[0])
            for attribute, value_list in attributes.items():
                for value in value_list:
                    print "%s: %s" % (attribute, value)
        except AlreadyAtRoot as e:
            print e
        except NoSuchDN as e:
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
