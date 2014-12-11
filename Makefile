

packages=commandline,node,connection

.PHONY: test
test:
	NOSE_COVER_PACKAGE="$(packages)" nosetests -v --with-coverage --cov-report term-missing

.PHONY: clean
clean:
	find . -name "*pyc" | xargs rm
