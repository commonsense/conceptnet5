DATE = $$(date +%Y%m%d_%H%M%S)
CSV_FILES = */data/flat/*.csv
DATA_SOURCES = conceptnet4 conceptnet4_nadya conceptnet4_zh dbpedia globalmind reverb verbosity wordnet wiktionary

all: data_sources core tar_bz_from_json

.PHONY: data_sources $(DATA_SOURCES)

data_sources: $(DATA_SOURCES)

$(DATA_SOURCES):
	$(MAKE) -C $@ all

conceptnet4_nadya: conceptnet4

core: data_sources
	python scripts/flat_assertions.py $(CSV_FILES)

tar_bz_from_json: core
	tar -cjf solr_json_$(DATE).tar.bz2 */data/solr/*.json data/solr/*.json

clean: force_look
	@for subdir in $(DATA_SOURCES);\
	do\
	    cd $$subdir/ ; make clean; cd ..;\
	done

	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*

force_look:
	true
