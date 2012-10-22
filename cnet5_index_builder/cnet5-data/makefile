DATE = $$(date +%Y%m%d_%H%M%S)
CSV_FILES = */data/flat/*.csv

#this distinction is made since cnet4 does not depend on any files 
#in the raw_data folder so the json would be rebuilt everytime
ALL_NON_CNET4_DATA_SOURCES  = conceptnet4_zh dbpedia globalmind reverb verbosity wordnet wiktionary
ALL_CNET4_DATA_SOURCES = conceptnet4 conceptnet4_nadya

non_cnet4_json:
	@for subdir in $(ALL_NON_CNET4_DATA_SOURCES);\
	do\
	    cd $$subdir/ ; make $$subdir_json;\
	done 
	
cnet4_json: 
		@for subdir in $(ALL_CNET4_DATA_SOURCES);\
	do\
	    cd $$subdir/ ; make $$subdir_json;\
	done


csv:
	@for subdir in $(ALL_CNET4_DATA_SOURCES) $(ALL_NON_CNET4_DATA_SOURCES);\
	do\
	    cd $$subdir/ ; make $$subdir_csv;\
	done

core: csv
	python scripts/flat_assertions.py $(CSV_FILES)

tar_bz_from_json: core
	tar -cjf solr_json_$(DATE).tar.bz2 */data/solr/*.json core_data/solr/*.json

clean: force_look
	@for subdir in $(ALL_CNET4_DATA_SOURCES) $(ALL_NON_CNET4_DATA_SOURCES);\
	do\
	    cd $$subdir/ ; make clean;\
	done

force_look:
	true
