#!/usr/bin/python

import unittest
import pexpect
import os
import sys
from ldapy.connection import Connection
import configuration

uri = configuration.uri
host = configuration.host
bind_dn = configuration.admin
password = configuration.admin_password

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
        self.sendline (command)
        self.expect ("\n")
        return self.expect_prompt ()

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
            l = p.container ()

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
