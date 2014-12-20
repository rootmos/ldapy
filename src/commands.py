
from commandline import Command
from ldapy import Ldapy

class List (Command):
    def __init__ (self, ldapy):
        Command.__init__ (self, "ls")
        self.ldapy = ldapy

    def __call__ (self, args):
        print "\t".join (self.ldapy.children)

class ChangeDN (Command):
    def __init__ (self, ldapy):
        Command.__init__ (self, "cd")
        self.ldapy = ldapy

    def __call__ (self, args):
        self.ldapy.changeDN (args[0])

class PrintWorkingDN (Command):
    def __init__ (self, ldapy):
        Command.__init__ (self, "pwd")
        self.ldapy = ldapy

    def __call__ (self, args):
        print self.ldapy.cwd
