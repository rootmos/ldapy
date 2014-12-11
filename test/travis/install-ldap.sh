#!/bin/sh -x

pwd
sudo DEBIAN_FRONTEND=noninteractive apt-get install slapd ldap-utils
sudo ldapadd -Y EXTERNAL -H ldapi:/// -f test/travis/ldap_db_init.ldif
sudo ldapadd -x -D cn=admin,dc=nodomain -w foobar -f test/data.ldif

