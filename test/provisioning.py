import ldap
import ldap.modlist
import collections
import random

# Example:
#    with provision("ldap://localhost", "cn=admin,dc=nodomain", "foobar") as p:
#        c = p.container(attr={"description":"foo"})
#        l = p.leaf(c, attr={"description":"bar"})

def salt():
    rng = random.SystemRandom()
    return rng.randrange(100000000)

class LdapObject(object):
    def __repr__(self):
        return self.dn

    def __iter__(self):
        return
        yield

class Container(LdapObject):
    def __init__(self, parent, name, objectClass, dnComponent, attr, anAttribute):
        if name:
            self.name = name
        else:
            self.name = "Container%s" % salt()

        self.objectClass = objectClass
        self.dnComponent = dnComponent
        self.anAttribute = anAttribute
        self.parent = parent
        self.rdn = "%s=%s" % (dnComponent, self.name)
        self.dn = "%s,%s" % (self.rdn, parent)

        if attr:
            self.attr = attr
        else:
            self.attr = {}
        self.attr["objectClass"] = objectClass
        self.attr[dnComponent] = self.name

        self.children = []

    def append(self, child):
        self.children.append(self.children)

    def __iter__(self):
        return self.children.__iter__()

class Leaf(LdapObject):
    def __init__(self, parent, name, objectClass, dnComponent, attr, anAttribute):
        if name:
            self.name = name
        else:
            self.name = "Leaf%s" % salt()

        self.objectClass = objectClass
        self.dnComponent = dnComponent
        self.anAttribute = anAttribute
        self.parent = parent
        self.rdn = "%s=%s" % (dnComponent, self.name)
        self.dn = "%s,%s" % (self.rdn, parent)

        if attr:
            self.attr = attr
        else:
            self.attr = {}
        self.attr["objectClass"] = objectClass
        self.attr[dnComponent] = self.name

class Provisioning:
    def __init__(self, uri, bindDN, password):
        self.ldap = ldap.initialize (uri)
        self.ldap.simple_bind_s (bindDN, password)
        self.provisionedDNs = collections.deque()
    
    def add(self, obj):
        ldif = ldap.modlist.addModlist(obj.attr)
        self.ldap.add_s(obj.dn, ldif)
        self.provisionedDNs.appendleft(obj)
    
    def delete(self, dn):
        try:
            results = self.ldap.search_s(str(dn), ldap.SCOPE_BASE)
            print "DEBUG: Deleting object %s: %s" % (dn, results)

            self.ldap.delete_s(str(dn))
        except ldap.NO_SUCH_OBJECT:
            print "WARNING: %s already deleted" % dn

    def attribute(self, dn, attribute):
        results = self.ldap.search_s(str(dn), ldap.SCOPE_BASE, attrlist = [attribute])
        _, attributes = results[0]
        try:
            return attributes[attribute]
        except KeyError:
            return []

    def exists (self, dn):
        try:
            result = self.ldap.search_s(str(dn), ldap.SCOPE_BASE, attrlist = ["objectClass"])
            assert result[0][1]["objectClass"]
            return True
        except ldap.NO_SUCH_OBJECT:
            return False


    def container(self, parent = None, name = None,
            objectClass = "organizationalUnit", dnComponent="ou",
            anAttribute = "description", attr = None):
        if not parent:
            parent = self.root
        
        c = Container(parent, name=name, attr=attr, objectClass = objectClass,
                dnComponent = dnComponent, anAttribute = anAttribute)
        self.add(c)
        return c

    def leaf(self, parent = None, name = None,
            objectClass = "organizationalRole", dnComponent="cn",
            anAttribute = "description", attr = None):
        if not parent:
            parent = self.root
        
        l = Leaf(parent, name=name, attr=attr, objectClass=objectClass,
                dnComponent=dnComponent, anAttribute=anAttribute)
        self.add(l)
        return l

    def unprovision(self):
        for obj in self.provisionedDNs:
            self.delete(obj)
        
    @property
    def root(self):
        results = self.ldap.search_s ("", ldap.SCOPE_BASE, attrlist = ["namingContexts"])
        roots = results[0][1]["namingContexts"]
        return roots[0]

class provision():
    def __init__(self, uri, bindDN, password):
        self.p = Provisioning(uri, bindDN, password)

    def __enter__(self):
        return self.p

    def __exit__(self, type, value, traceback):
        self.p.unprovision()
        return False

