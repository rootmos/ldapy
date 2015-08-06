
packages=ldapy

.PHONY: test
test:
	rm -f .coverage
	NOSE_COVER_PACKAGE="$(packages)" nosetests -v --with-coverage --cov-report term-missing

.PHONY: dist
dist: clean-dist
	python setup.py bdist_wheel --universal

.PHONY: clean-dist
clean-dist:
	rm -rf dist/*

.PHONY: requirements
requirements:
	pip install -r requirements.txt --quiet

.PHONY: install
install: dist requirements
	pip install --user dist/*

.PHONY: upgrade
upgrade: dist requirements
	pip install --user --upgrade dist/*

.PHONY: clean
clean:
	find . -name "*pyc" | xargs rm
