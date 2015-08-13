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

This will try to:

1. Install all requirements (see the `requirements.txt` file) using `pip`
2. Gather a distribution file with `python setup.py`
3. Install `ldapy` using `pip`

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

Wishlist
--------
* Save recent connections, let user override settings in them (eg reuse all
  settings but change the bind DN.) This feature is ongoing in the
  connection-data branch.
* Rename and move DNs
* Wildcards
* Release 0.1 :)

