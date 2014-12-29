#!/bin/sh -x

sudo apt-get purge slapd ldap-utils
sudo DEBIAN_FRONTEND=noninteractive apt-get install slapd ldap-utils

sudo ldapmodify -Y EXTERNAL -H ldapi:/// -f test/travis/change_pwd.ldif
sudo ldapadd -x -D cn=admin,dc=nodomain -w foobar -f test/data.ldif

