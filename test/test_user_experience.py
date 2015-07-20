#!/usr/bin/python

import unittest
import pexpect
import os
import sys
from ldapy.connection import Connection
import configuration
import random
import string

uri = configuration.uri
host = configuration.host
bind_dn = configuration.admin
password = configuration.admin_password

def random_value (N=20):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))


class spawn_ldapy (pexpect.spawn):
    def __init__ (self, args = None, root = None, wait_for_prompt=True):
        pwd = os.path.dirname (__file__)
        script = os.path.join (pwd, "../scripts/ldapy")
        coverage = ["coverage", "run", "-p", "--source", os.environ["NOSE_COVER_PACKAGE"], script]

        if not args:
            args = ["-D", bind_dn, "-w", password, uri ]

        pexpect.spawn.__init__ (self, " ".join (coverage + args),
                env = {"PYTHONPATH" : ":".join(sys.path)})

        if root:
            self.expect_prompt()
            self.sendline ("cd %s" % root)

        if wait_for_prompt:
            self.expect_prompt()

    def expect_prompt (self):
        self.expect ("\$", timeout=5)
        return self.before.splitlines()

    def assert_exitstatus (self, status):
        if self.isalive():
            self.wait()

        assert self.exitstatus == status

    def send_command (self, command):
        print "Sending command: ", command
        self.sendline (command)
        self.expect ("\n")
        lines = self.expect_prompt ()
        print "Received lines: ", lines
        return lines

    def __enter__ (self):
        return self

    def __exit__(self, type, value, traceback):
        if self.isalive():
            self.sendline ("quit")
            self.assert_exitstatus (0)
        return False

class BasicConnectivity (unittest.TestCase):

    def test_successful_anonymous_connection (self):
        self.execute_with_args_ls_and_expect_root ([uri]) 

    def test_successful_bind_with_uri (self):
        self.execute_with_args_ls_and_expect_root (["-D", bind_dn, "-w", password, uri ])

    def test_successful_bind_with_host_port (self):
        self.execute_with_args_ls_and_expect_root (["-D", bind_dn, "-w", password, "-H", host])

    def execute_with_args_ls_and_expect_root (self, args):
        with configuration.provision() as p, spawn_ldapy (args=args) as ldapy:
            ldapy.sendline ("ls")
            ldapy.expect (p.root)
            ldapy.expect_prompt ()

class FailedConnectionErrors (unittest.TestCase):
    def test_unknow_host (self):
        bad_uri = "ldap://foobar"
        args = [bad_uri]
        with spawn_ldapy (args=args, wait_for_prompt=False) as ldapy:
            ldapy.expect (Connection._connection_error_msg % bad_uri)
            ldapy.assert_exitstatus (1)

    def test_auth_failed (self):
        args = [uri, "-D", bind_dn, "-w", "wrong"]
        with spawn_ldapy (args=args, wait_for_prompt=False) as ldapy:
            ldapy.expect (Connection._bad_auth_error_msg % bind_dn)
            ldapy.assert_exitstatus (1)

    def test_auth_with_no_password (self):
        args = [uri, "-D", bind_dn]
        with spawn_ldapy (args=args, wait_for_prompt=False) as ldapy:
            ldapy.expect (Connection._server_unwilling)
            ldapy.assert_exitstatus (1)

class LoggingLevels (unittest.TestCase):
    def test_no_logging_when_not_asked (self):
        args = [uri]
        with spawn_ldapy (args=args, wait_for_prompt=False) as ldapy:
            with self.assertRaises (pexpect.TIMEOUT):
                ldapy.expect (["INFO", "DEBUG"], timeout=1)

    def test_verbose_info (self):
        args = ["-v", uri]
        with spawn_ldapy (args=args, wait_for_prompt=False) as ldapy:
            ldapy.expect ("INFO")

    def test_debug_info (self):
        args = ["-d", uri]
        with spawn_ldapy (args=args, wait_for_prompt=False) as ldapy:
            ldapy.expect ("DEBUG")

class NavigationUseCases (unittest.TestCase):
    def test_cd_and_pwd (self):
        with configuration.provision() as p, spawn_ldapy(root=p.root) as ldapy:
            c = p.container ()

            lines = ldapy.send_command ("pwd")
            self.assertListEqual([p.root], lines)

            ldapy.send_command ("cd %s" % c.rdn)
            lines = ldapy.send_command ("pwd")
            self.assertListEqual([c.dn], lines)

            ldapy.send_command ("cd .")
            lines = ldapy.send_command ("pwd")
            self.assertListEqual([c.dn], lines)

            ldapy.send_command ("cd ..")
            lines = ldapy.send_command ("pwd")
            self.assertListEqual([p.root], lines)

class CatUseCases (unittest.TestCase):
    def test_cat_contains_attributes (self):
        with configuration.provision() as p, spawn_ldapy(root=p.root) as ldapy:
            c = p.container ()
            l = p.leaf (c)
            ldapy.send_command ("cd %s" % c.rdn)

            lines = ldapy.send_command ("cat .")
            foundName = False
            foundObjectClass = False
            for line in lines:
                if c.dnComponent in line and c.name in line:
                    foundName = True
                elif "objectClass" in line and c.objectClass in line:
                    foundObjectClass = True
            self.assertTrue (foundName)
            self.assertTrue (foundObjectClass)

            lines = ldapy.send_command ("cat %s" % l.rdn)
            foundName = False
            foundObjectClass = False
            for line in lines:
                if l.dnComponent in line and l.name in line:
                    foundName = True
                elif "objectClass" in line and l.objectClass in line:
                    foundObjectClass = True
            self.assertTrue (foundName)
            self.assertTrue (foundObjectClass)

class ModifyUseCases (unittest.TestCase):
    def verify_attribute (self, ldapy, rdn, attribute, value = None):
        lines = ldapy.send_command ("cat %s" % rdn)

        found = False
        for line in lines:
            if attribute in line:
                if value is not None:
                    if value in line:
                        found = True
                else:
                    found = True

        return found

    def test_modify (self):
        with configuration.provision() as p, spawn_ldapy(root=p.root) as ldapy:
            l = p.leaf ()
            attribute = l.anAttribute
            value1_1 = random_value()
            value1_2 = random_value()
            value2 = random_value()

            # Verify attribute does not exist
            self.assertFalse(self.verify_attribute (ldapy, l.rdn, attribute))

            # Add the first value
            ldapy.send_command ("modify %s add %s %s" % (l.rdn, attribute, value1_1))
            self.assertTrue(self.verify_attribute (ldapy, l.rdn, attribute, value = value1_1))
            self.assertFalse(self.verify_attribute (ldapy, l.rdn, attribute, value = value2))

            # Add the second value
            ldapy.send_command ("modify %s add %s %s" % (l.rdn, attribute, value2))
            self.assertTrue(self.verify_attribute (ldapy, l.rdn, attribute, value = value1_1))
            self.assertTrue(self.verify_attribute (ldapy, l.rdn, attribute, value = value2))

            # Replace the first value
            ldapy.send_command ("modify %s replace %s %s %s" % (l.rdn, attribute, value1_1, value1_2))
            self.assertFalse(self.verify_attribute (ldapy, l.rdn, attribute, value = value1_1))
            self.assertTrue(self.verify_attribute (ldapy, l.rdn, attribute, value = value1_2))
            self.assertTrue(self.verify_attribute (ldapy, l.rdn, attribute, value = value2))

            # Delete the first value
            ldapy.send_command ("modify %s delete %s %s" % (l.rdn, attribute, value1_2))
            self.assertFalse(self.verify_attribute (ldapy, l.rdn, attribute, value = value1_2))
            self.assertTrue(self.verify_attribute (ldapy, l.rdn, attribute, value = value2))

            # Delete the second value
            ldapy.send_command ("modify %s delete %s %s" % (l.rdn, attribute, value2))
            self.assertFalse(self.verify_attribute (ldapy, l.rdn, attribute, value = value1_2))
            self.assertFalse(self.verify_attribute (ldapy, l.rdn, attribute, value = value2))

            # Verify we have nothing left
            self.assertFalse(self.verify_attribute (ldapy, l.rdn, attribute))

class DeleteUseCases (unittest.TestCase):
    def test_delete (self):
        with configuration.provision() as p, spawn_ldapy(root=p.root) as ldapy:
            c = p.container ()
            l1 = p.leaf (c)
            l2 = p.leaf (c)
            ldapy.send_command ("cd %s" % c.rdn)

            self.assertTrue(p.exists (l1))
            self.assertTrue(p.exists (l2))

            ldapy.send_command ("delete %s" % l1.rdn)

            self.assertFalse(p.exists (l1))
            self.assertTrue(p.exists (l2))


class AddUseCases (unittest.TestCase):
    def test_add (self):
        with configuration.provision() as p, spawn_ldapy(root=p.root) as ldapy:
            c = p.container ()
            ldapy.send_command ("cd %s" % c.rdn)

            name = random_value()
            dnComponent = "cn"
            objectClass = "organizationalRole"
            rdn = "%s=%s" % (dnComponent, name)
            dn = "%s,%s" % (rdn, c.dn)

            anAttribute = "description"
            anAttributeValue = random_value()

            fmt = "%s:%s"
            attributesList = [fmt % (dnComponent, name),
                              fmt % ("objectClass", objectClass),
                              fmt % (anAttribute, anAttributeValue)]
            attributes = " ".join (attributesList)

            try:
                self.assertFalse(p.exists(dn))
                ldapy.send_command ("add %s %s" % (rdn, attributes))
                self.assertTrue(p.exists(dn))
                self.assertEquals([name], p.attribute (dn, dnComponent))
                self.assertEquals([objectClass], p.attribute (dn, "objectClass"))
                self.assertEquals([anAttributeValue], p.attribute (dn, anAttribute))
            finally:
                p.delete (dn)

