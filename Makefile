

packages=ldapy

.PHONY: test
test:
	rm -f .coverage
	NOSE_COVER_PACKAGE="$(packages)" nosetests -v --with-coverage --cov-report term-missing

.PHONY: clean
clean:
	find . -name "*pyc" | xargs rm
