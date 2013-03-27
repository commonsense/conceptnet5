DATE = $$(date +%Y%m%d)
CSV_FILES = */data/flat/*.csv
DATA_SOURCES = conceptnet4 conceptnet4_nadya conceptnet4_zh dbpedia globalmind reverb verbosity wordnet wiktionary
FORMAT_TAR_FILES = --transform='s\#.*/\#\#'
OUTPUT_FOLDER = $(DATE)
DOWNLOAD_SERVER_AND_DIRECTORY = jvarley@salmon.media.mit.edu:/var/www/conceptnet5/downloads/
CORE = data/flat/*.json

#just naming phony targets, meaning these targets do not correspond to real files,
# i.e., there is not file called data_sources
.PHONY: all data_sources $(DATA_SOURCES) output_directory tar_bz_solr tar_bz_flat tar_bz_csv clean create_output_directory


########################################################
# This runs through the 3 main parts of the build process
all: data_sources core package_all

########################################################
# This goes through all the directories for the different sources.
# It converts the different sources into conceptnet5 assertions,
# and creates the flat_json, solr_json, and csv files
data_sources: $(DATA_SOURCES)

$(DATA_SOURCES):
	$(MAKE) -C $@ all

conceptnet4_nadya: conceptnet4

########################################################
# This builds the core, which is a concatenation of all the csv assertions,
# where duplicate assertions have their weights aggregated
core: $(CORE)

$(CORE): data_sources
	touch data/temp/abc123xyz
	-rm data/temp/*
	python scripts/flat_assertions.py $(CSV_FILES)

########################################################
# This packages up all of the solr,json, and csv files as well as the core
# into a single directory with 3 tar.bz2's it also creates a checksum for these files
package_all: create_output_directory tar_files md5_checksum

tar_files: tar_bz_solr tar_bz_flat tar_bz_csv

create_output_directory:
	mkdir -p $(OUTPUT_FOLDER)

tar_bz_solr: 
	tar -cjf $(OUTPUT_FOLDER)/solr_json_$(DATE).tar.bz2 */data/solr/*.json data/solr/*.json $(FORMAT_TAR_FILES)

tar_bz_flat: 
	tar -cjf $(OUTPUT_FOLDER)/flat_json_$(DATE).tar.bz2 */data/flat/*.json data/flat/*.json $(FORMAT_TAR_FILES)

tar_bz_csv: 
	tar -cjf $(OUTPUT_FOLDER)/csv_$(DATE).tar.bz2 */data/flat/*.csv $(FORMAT_TAR_FILES)

md5_checksum: tar_bz_csv tar_bz_flat tar_bz_solr
	md5sum $(OUTPUT_FOLDER)/*.tar.bz2 >> $(OUTPUT_FOLDER)/md5sum.txt

#########################################################
#This command will run the script to copy the output directory over to salmon
#this requires that you are running as jvarley on amber, so that a password is not required
export_output:
	scp -r $(OUTPUT_FOLDER) $(DOWNLOAD_SERVER_AND_DIRECTORY)

########################################################	
# This gets rid of all intermediate files
clean:
	@for subdir in $(DATA_SOURCES);\
	do\
	    cd $$subdir/ ; $(MAKE) clean; cd ..;\
	done

	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*
	-rm data/temp/*
