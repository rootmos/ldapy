#!/usr/bin/python

import unittest
import pexpect
import os

def create_ldapy_process (args):
    pwd = os.path.dirname (__file__)
    script = os.path.join (pwd, "../src/ldapy")
    coverage = ["coverage", "run", "-p", "--source", os.environ["NOSE_COVER_PACKAGE"], script]

    return pexpect.spawn (" ".join (coverage + args))

uri = "ldap://localhost"
host = "localhost"
bind_dn = "cn=admin,dc=nodomain"
root = "dc=nodomain"
password = "foobar"

class BasicConnectivity (unittest.TestCase):

    def test_successful_anonymous_connection (self):
        self.execute_with_args_ls_and_expect_root ([uri]) 

    def test_successful_bind_with_uri (self):
        self.execute_with_args_ls_and_expect_root (["-D", bind_dn, "-w", password, uri ])

    def test_successful_bind_with_host_port (self):
        self.execute_with_args_ls_and_expect_root (["-D", bind_dn, "-w", password, "-H", host])

    def execute_with_args_ls_and_expect_root (self, args):
        ldapy = create_ldapy_process (args)

        ldapy.expect ("\$")
        ldapy.sendline ("ls")
        ldapy.expect (root)

        ldapy.expect ("\$")
        ldapy.sendline ("quit")

        ldapy.wait ()

        assert ldapy.exitstatus == 0

