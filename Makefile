

packages=commandline,node,connection

.PHONY: test
test:
	nosetests -v --with-coverage --cover-package=$(packages) --cov-report term-missing

.PHONY: clean
clean:
	find . -name "*pyc" | xargs rm
