ldapy
=====

[![Build Status](https://travis-ci.org/rootmos/ldapy.svg)](https://travis-ci.org/rootmos/ldapy)
[![Coverage Status](https://coveralls.io/repos/rootmos/ldapy/badge.png)](https://coveralls.io/r/rootmos/ldapy)

`ldapy` is aimed to be command line LDAP explorer implemented in Python, with
all the joys of GNU readline: history, completion and editing.
Heavily inspired by [shelldap](http://projects.martini.nu/shelldap).

Installation
------------
Installation should be as easy as:
```
make install
```
This will try to execute `python setup.py install --user` to install it for the
current user.

If there's missing dependencies (see the `requirements.txt` file), these can
easily be resolved by using `pip`, conveniently wrapped as a make-target:
```
make requirements
```

The primary requirements are
[python-ldap](http://www.python-ldap.org/doc/html/ldap.html) and
[readline](https://docs.python.org/2/library/readline.html).

Usage
-----
Usage information can be found by executing
```
ldapy --help
```

But for the impatient, here's an example:
```
ldapy --host=localhost --bind-dn cn=Admin,dc=nodomain --password=foobar
```
After a successful connection you'll see a prompt `$`, where you can use the
familiar shell commands: `ls`, `cd`, `pwd`, `cat`.
To modify the data the commands: `modify`, `add` and `delete` are available.
All of these commands can be asked to be helpful: `ls --help`.

To make it easier to connect you can use previous connections:
```
ldapy                # will use the most recent connection
ldapy --previous     # lists the previous connections
ldapy --previous 2   # connect with the third most recent connection (zero-indexing)
```

You can also save your favorite connections:
```
ldapy --save 1 foo   # stores the second most recent connection as "foo"
ldapy --saved        # lists all saved connections
ldapy --saved foo    # connect using the save connection "foo"
ldapy --remove foo   # remove the saved connection "foo"
```

Wishlist
--------
* Allow combinations of stored connections and specified connection data
* Rename and move DNs
* Wildcards
* Compatibility with Python3

