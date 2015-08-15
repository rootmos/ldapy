
packages=ldapy

.PHONY: test
test:
	rm -f .coverage
	NOSE_COVER_PACKAGE="$(packages)" nosetests -v --with-coverage --cov-report term-missing

.PHONY: install
install:
	python setup.py install --user

.PHONY: requirements
requirements:
	pip install -r requirements.txt --quiet

.PHONY: clean
clean:
	find . -name "*pyc" | xargs rm
