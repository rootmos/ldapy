
from commandline import Command
from ldapy import Ldapy, NoSuchDN, AlreadyAtRoot

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
        try:
            self.ldapy.changeDN (args[0])
        except AlreadyAtRoot as e:
            print e
        except NoSuchDN as e:
            print e

class PrintWorkingDN (Command):
    def __init__ (self, ldapy):
        Command.__init__ (self, "pwd")
        self.ldapy = ldapy

    def __call__ (self, args):
        print self.ldapy.cwd

class Cat (Command):
    def __init__ (self, ldapy):
        Command.__init__ (self, "cat")
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

