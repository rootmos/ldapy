

packages=commandline,node,connection,ldapy

.PHONY: test
test:
	NOSE_COVER_PACKAGE="$(packages)" nosetests -v --with-coverage --cov-report term-missing

.PHONY: clean
clean:
	find . -name "*pyc" | xargs rm

.PHONY: dump
dump:
	###########################################################################
	sudo slapcat
	###########################################################################
	tail -100 /var/log/syslog
	###########################################################################
