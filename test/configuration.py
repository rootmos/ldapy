from ldapy.connection import Connection

uri = "ldap://localhost"
admin = "cn=admin,dc=nodomain"
admin_password = "foobar"

def getConnection (traces = 0):
    con = Connection (uri, traces)
    con.bind (admin, admin_password)
    return con

