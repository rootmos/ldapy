

packages=commandline,node,connection

.PHONY: test
test:
	nosetests --with-coverage --cover-package=$(packages)

.PHONY: clean
clean:
	find . -name "*pyc" | xargs rm
