import connection

uri = "ldap://localhost"
admin = "cn=admin,dc=nodomain"
admin_password = "foobar"

def getConnection (traces = 0):
    con = connection.Connection (uri, traces)
    con.bind (admin, admin_password)
    return con

