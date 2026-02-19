SHELL := /bin/bash 
DEST=.
PYTHON=python3
PACKAGE?=sbompy

.PHONY: create create-html create-md clean-html clean-md host


create: create-html create-md

clean: clean-html clean-md

create-html: 
	pdoc3 $(PACKAGE) --html -o $(DEST)/html --skip-errors

create-md: 
	pdoc3 $(PACKAGE) -o $(DEST)/markdown --skip-errors

clean-html:
	rm -rf $(DEST)/html

clean-md:
	rm -rf $(DEST)/markdown

host: 
	cd $(DEST)/html/$(PACKAGE) && $(PYTHON) -m http.server 8500

