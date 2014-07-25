# A Makefile for installing apsw, a SQLite 3 wrapper that we can use to
# write ConceptNet databases more efficiently.

APSW_VERSION = 3.8.5-r1
APSW_NAME = apsw-$(APSW_VERSION)

UNTAR = tar xvf
PYTHON = python

apsw: $(APSW_NAME)/build

clean:
	rm -rf $(APSW_NAME)

$(APSW_NAME)/build: $(APSW_NAME)/setup.py
	cd $(APSW_NAME) && $(PYTHON) setup.py fetch --sqlite install

$(APSW_NAME)/setup.py: $(APSW_NAME).tar.gz
	rm -rf $(APSW_NAME)
	$(UNTAR) $<
	touch $(APSW_NAME)/setup.py
