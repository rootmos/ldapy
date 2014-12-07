import connection

uri = "ldap://localhost"
admin = "cn=admin,dc=nodomain"
admin_password = "foobar"

def getConnection ():
    con = connection.Connection (uri)
    con.bind (admin, admin_password)
    return con

