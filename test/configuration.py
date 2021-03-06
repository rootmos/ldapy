import provisioning
from ldapy.connection import Connection

host = "localhost"
uri = "ldap://%s" % host
admin = "cn=admin,dc=nodomain"
admin_password = "foobar"

def getConnection (traces = 0):
    con = Connection (uri, traces)
    con.bind (admin, admin_password)
    return con

def provision ():
    return provisioning.provision(uri, admin, admin_password)

