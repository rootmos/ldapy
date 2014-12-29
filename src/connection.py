import ldap
import sys

import logging
logger = logging.getLogger("ldapy").getChild (__name__)

class ConnectionError (Exception):
    def __init__ (self, con, msg, info = None):
        self.con = con
        self.msg = msg
        self.info = info

    def __str__ (self):
        if self.info:
            return self.msg + " Info: " + self.info
        else:
            return self.msg

class Connection:
    """The class managing the LDAP connection."""

    _connection_error_msg = "Unable to connect to %s."
    _bad_auth_error_msg = "Unable to authenticate user: %s."
    _server_unwilling = "Server unwilling to perform requested operation."

    def __init__ (self, uri, traces = 0):
        logger.info ("Connecting to %s" % uri)
        self.uri = uri
        self.ldap = ldap.initialize (uri, trace_level = traces, trace_file = sys.stdout)
        self.connected = False
        self._roots = None

    def _raise_error (self, msg, exception = None):
        if exception and hasattr(exception, "message") and exception.message.has_key ("info"):
            raise ConnectionError (self, msg, exception.message["info"])
        else:
            raise ConnectionError (self, msg)


    def bind (self, who, cred):
        try:
            self.ldap.simple_bind_s (who, cred)
        except ldap.SERVER_DOWN as e:
            self._raise_error (Connection._connection_error_msg % self.uri, e)
        except ldap.INVALID_CREDENTIALS as e:
            self._raise_error (Connection._bad_auth_error_msg % who, e)
        except ldap.UNWILLING_TO_PERFORM as e:
            self._raise_error (Connection._server_unwilling, e)

        self.connected = True

    @property
    def roots (self):
        if not self._roots:
            results = self.ldap.search_s ("", ldap.SCOPE_BASE, attrlist = ["namingContexts"])
            self._roots = results[0][1]["namingContexts"]

            logger.debug ("Roots: %s" % self._roots)

        return self._roots

