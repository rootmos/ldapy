
.PHONY: test
test:
	nosetests

.PHONY: clean
clean:
	find . -name "*pyc" | xargs rm
