

packages=commandline,node,connection

.PHONY: test
test:
	nosetests --with-coverage --cover-package=$(packages) --cov-report term-missing

.PHONY: clean
clean:
	find . -name "*pyc" | xargs rm
