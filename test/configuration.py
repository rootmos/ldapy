import connection

uri = "ldap://localhost"
admin = "cn=admin,dc=nodomain"
admin_password = "foobar"

def getConnection ():
    con = connection.Connection (uri, 2)
    con.bind (admin, admin_password)
    return con

