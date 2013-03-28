#all the csv files used to build the core
CSV_FILES_TO_MAKE_CORE = */data/flat/*.csv
#all the data sources that conceptnet5 builds from
DATA_SOURCES = conceptnet4 conceptnet4_nadya conceptnet4_zh dbpedia globalmind reverb verbosity wordnet wiktionary
#used to get rid of the directory structure inside the tar files, so the tar file is just a list of files
FORMAT_TAR_FILES = --transform='s\#.*/\#\#'
#this folder will be something like 20130304 which contains 3 tars and md5sum.txt
OUTPUT_FOLDER = $$(date +%Y%m%d)
#This is where we place the finished build so that it can be downloaded by anyone
DOWNLOAD_SERVER_AND_DIRECTORY = jvarley@salmon.media.mit.edu:/var/www/conceptnet5/downloads/
#these are the files that we want to upload to solr.
SOLR_UPLOAD_FILES =  */data/solr/*.json data/solr/*.json

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
core: data_sources clear_temp_directory_used_to_make_core
	python scripts/build_core_from_csvs.py $(CSV_FILES_TO_MAKE_CORE)

# core requires pulling all assertions into memory, so easier 
# to do this in several passes, and use some temp files in the process.
# we want to make sure this directory is empty before we start making the core.
clear_temp_directory_used_to_make_core:
	touch data/temp/abc123xyz
	-rm data/temp/*

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
export_output_for_download:
	scp -r $(OUTPUT_FOLDER) $(DOWNLOAD_SERVER_AND_DIRECTORY)

##########################################################
#this command will repopulate all the solr indices
repopulate_solr: clear_solr_salmon upload_solr_salmon clear_solr_burgundy upload_solr_burgundy clear_solr_claret upload_solr_claret

##########################################################
# These commands will remove all the current entries from the solr index,
# so that the index can be repopulated with the new build
clear_solr_salmon:
	curl "http://salmon.media.mit.edu:8983/solr/update?commit=true" -H "Content-Type: text/xml" --data-binary  '<delete><query>*:*</query></delete>'

clear_solr_burgundy:
	curl "http://burgundy.media.mit.edu:8983/solr/update?commit=true" -H "Content-Type: text/xml" --data-binary  '<delete><query>*:*</query></delete>'

clear_solr_claret:
	curl "http://claret.media.mit.edu:8983/solr/update?commit=true" -H "Content-Type: text/xml" --data-binary  '<delete><query>*:*</query></delete>'

########################################################
# These commands will upload the new build files into the solr index,
#curl 'http://salmon.media.mit.edu:8983/solr/update/json?commit=true' --data-binary @$i -H 'Content-type:application/json'
upload_solr_salmon:
	@for solr_file in $(SOLR_UPLOAD_FILES);\
	do\
		echo Importing $$solr_file;\
		curl 'http://salmon.media.mit.edu:8983/solr/update/json?commit=true' --data-binary $$solr_file -H 'Content-type:application/json';\
	done

upload_solr_burgundy:
	@for solr_file in $(SOLR_UPLOAD_FILES);\
	do\
		echo Importing $$solr_file;\
		curl 'http://burgundy.media.mit.edu:8983/solr/update/json?commit=true' --data-binary $$solr_file -H 'Content-type:application/json';\
	done

upload_solr_claret: 
	@for solr_file in $(SOLR_UPLOAD_FILES);\
	do\
		echo Importing $$solr_file;\
		curl 'http://claret.media.mit.edu:8983/solr/update/json?commit=true' --data-binary $$solr_file -H 'Content-type:application/json';\
	done

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
