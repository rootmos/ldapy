#!/usr/bin/python

import unittest
import pexpect
import os
import sys
from ldapy.connection import Connection
import configuration

def create_ldapy_process (args):
    pwd = os.path.dirname (__file__)
    script = os.path.join (pwd, "../scripts/ldapy")
    coverage = ["coverage", "run", "-p", "--source", os.environ["NOSE_COVER_PACKAGE"], script]

    return pexpect.spawn (" ".join (coverage + args), env = {"PYTHONPATH" : ":".join(sys.path)})

uri = configuration.uri
host = configuration.host
bind_dn = configuration.admin
password = configuration.admin_password

class BasicConnectivity (unittest.TestCase):

    def test_successful_anonymous_connection (self):
        self.execute_with_args_ls_and_expect_root ([uri]) 

    def test_successful_bind_with_uri (self):
        self.execute_with_args_ls_and_expect_root (["-D", bind_dn, "-w", password, uri ])

    def test_successful_bind_with_host_port (self):
        self.execute_with_args_ls_and_expect_root (["-D", bind_dn, "-w", password, "-H", host])

    def execute_with_args_ls_and_expect_root (self, args):
        with configuration.provision() as p:
            ldapy = create_ldapy_process (args)

            ldapy.expect ("\$")
            ldapy.sendline ("ls")
            ldapy.expect (p.root)

            ldapy.expect ("\$")
            ldapy.sendline ("quit")

            ldapy.wait ()

            assert ldapy.exitstatus == 0

class FailedConnectionErrors (unittest.TestCase):
    def test_unknow_host (self):
        bad_uri = "ldap://foobar"
        ldapy = create_ldapy_process ([bad_uri])
        ldapy.expect (Connection._connection_error_msg % bad_uri)
        ldapy.wait ()
        assert ldapy.exitstatus == 1

    def test_auth_failed (self):
        ldapy = create_ldapy_process ([uri, "-D", bind_dn, "-w", "wrong"])
        ldapy.expect (Connection._bad_auth_error_msg % bind_dn)
        ldapy.wait ()
        assert ldapy.exitstatus == 1

    def test_auth_with_no_password (self):
        ldapy = create_ldapy_process ([uri, "-D", bind_dn])
        ldapy.expect (Connection._server_unwilling)
        ldapy.wait ()
        assert ldapy.exitstatus == 1

class LoggingLevels (unittest.TestCase):
    def test_no_logging_when_not_asked (self):
        ldapy = create_ldapy_process ([uri])
        with self.assertRaises (pexpect.TIMEOUT):
            ldapy.expect (["INFO", "DEBUG"], timeout=1)

    def test_verbose_info (self):
        ldapy = create_ldapy_process (["-v", uri])
        ldapy.expect ("INFO")

    def test_debug_info (self):
        ldapy = create_ldapy_process (["-d", uri])
        ldapy.expect ("DEBUG")

