import ldap

class ConnectionError(Exception):
    def __init__ (self, con, msg):
        self.con = con
        self.msg = msg

    def __str__ (self):
        return "Connection(\"%s\"): %s" % (self.con.uri, self.msg)

class Connection:
    """The class managing the LDAP connection."""

    _connection_error_msg = "Unable to connect to %s"
    _bad_auth_error_msg = "Unable to authenticate user = %s"

    def __init__ (self, uri):
        self.uri = uri
        self.con = ldap.initialize (uri)
        self.connected = False

    def _raise_error (self, msg):
        raise ConnectionError (self, msg)

    def bind (self, who, cred):
        try:
            self.con.simple_bind_s (who, cred)
        except ldap.SERVER_DOWN:
            self._raise_error (Connection._connection_error_msg % self.uri)
        except ldap.INVALID_CREDENTIALS:
            self._raise_error (Connection._bad_auth_error_msg % who)

        self.connected = True

