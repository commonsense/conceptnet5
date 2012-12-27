DATE = $$(date +%Y%m%d)
CSV_FILES = */data/flat/*.csv
DATA_SOURCES = conceptnet4 conceptnet4_nadya conceptnet4_zh dbpedia globalmind reverb verbosity wordnet wiktionary
TRANSFORM = --transform='s\#.*/\#\#'
OUTPUT_FILE = conceptnet5_output_$(DATE)
CORE = data/flat/*.json

all: data_sources $(CORE) package_all

.PHONY: data_sources $(DATA_SOURCES) output_directory tar_bz_solr tar_bz_flat tar_bz_csv force_look

data_sources: $(DATA_SOURCES)

$(DATA_SOURCES):
	$(MAKE) -C $@ all

conceptnet4_nadya: conceptnet4

$(CORE): data_sources
	python scripts/flat_assertions.py $(CSV_FILES)

package_all: output_directory tar_bz_solr tar_bz_flat tar_bz_csv

output_directory: force_look
	mkdir -p $(OUTPUT_FILE)

tar_bz_solr: output_directory
	tar -cjf $(OUTPUT_FILE)/solr_json_$(DATE).tar.bz2 */data/solr/*.json data/solr/*.json $(TRANSFORM)

tar_bz_flat: output_directory
	tar -cjf $(OUTPUT_FILE)/flat_json_$(DATE).tar.bz2 */data/flat/*.json data/flat/*.json $(TRANSFORM)

tar_bz_csv: output_directory
	tar -cjf $(OUTPUT_FILE)/csv_$(DATE).tar.bz2 */data/flat/*.csv $(TRANSFORM)

clean: force_look
	@for subdir in $(DATA_SOURCES);\
	do\
	    cd $$subdir/ ; $(MAKE) clean; cd ..;\
	done

	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*

force_look:
	true
