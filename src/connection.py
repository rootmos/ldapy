import ldap

class Connection:
    """The class managing the LDAP connection."""

    def __init__ (self, uri):
        self.uri = uri
        self.con = ldap.initialize (uri)
        self.connected = False
        pass
