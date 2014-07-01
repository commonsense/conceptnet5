# A Makefile for installing apsw, a SQLite 3 wrapper that we can use to
# write ConceptNet databases more efficiently.

APSW_VERSION = 3.8.5-r1
APSW_NAME = apsw-$(APSW_VERSION)

UNZIP = unzip
PYTHON = python
CURL_DOWNLOAD = curl -LO
DOWNLOAD_LOC = https://github.com/rogerbinns/apsw/releases/download

apsw: $(APSW_NAME)/build

clean:
	rm -rf $(APSW_NAME) $(APSW_NAME).zip

$(APSW_NAME)/build: $(APSW_NAME)/setup.py
	cd $(APSW_NAME) && $(PYTHON) setup.py fetch --sqlite install

$(APSW_NAME)/setup.py: $(APSW_NAME).zip
	rm -rf $(APSW_NAME)
	$(UNZIP) $<
	touch $(APSW_NAME)/setup.py

$(APSW_NAME).zip:
	$(CURL_DOWNLOAD) $(DOWNLOAD_LOC)/$(APSW_VERSION)/$(APSW_NAME).zip
