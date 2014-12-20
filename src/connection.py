import ldap
import logging
import sys

class ConnectionError (Exception):
    def __init__ (self, con, msg):
        self.con = con
        self.msg = msg

    def __str__ (self):
        return "Connection(\"%s\"): %s" % (self.con.uri, self.msg)

class Connection:
    """The class managing the LDAP connection."""

    _connection_error_msg = "Unable to connect to %s"
    _bad_auth_error_msg = "Unable to authenticate user = %s"

    def __init__ (self, uri, traces = 0):
        logging.info ("Connecting to %s" % uri)
        self.uri = uri
        self.ldap = ldap.initialize (uri, trace_level = traces, trace_file = sys.stdout)
        self.connected = False
        self._roots = None

    def _raise_error (self, msg):
        raise ConnectionError (self, msg)

    def bind (self, who, cred):
        try:
            self.ldap.simple_bind_s (who, cred)
        except ldap.SERVER_DOWN:
            self._raise_error (Connection._connection_error_msg % self.uri)
        except ldap.INVALID_CREDENTIALS:
            self._raise_error (Connection._bad_auth_error_msg % who)

        self.connected = True

    @property
    def roots (self):
        if not self._roots:
            results = self.ldap.search_s ("", ldap.SCOPE_BASE, attrlist = ["namingContexts"])
            self._roots = results[0][1]["namingContexts"]

            logging.debug ("Roots: %s" % self._roots)

        return self._roots

