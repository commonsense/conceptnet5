PYTHON = python
READERS = ../conceptnet5/readers
BUILDERS = ../conceptnet5/builders
DATE = $(shell date +%Y%m%d)
OUTPUT_FOLDER = dist/$(DATE)
DOWNLOAD_SSH_LOC = conceptnet5.media.mit.edu:/var/www/conceptnet5/downloads
DOWNLOAD_URL = http://conceptnet5.media.mit.edu/downloads
RAW_DATA_PACKAGE = conceptnet5-raw-data.tar.bz2
ASSOC_DIR = assoc/assoc-space-5.2

# File names
# ==========
# The Makefile's job is to turn files into other files. In order for it
# to do its job, you have to say which files those are, before they exist.
# So the following variables collectively define the files that the Makefile
# is responsible for building.
#
# There's a subtlety about Makefiles going on here: Assigning a variable
# with := assigns it immediately, while = figures it out lazily when the
# variable is actually needed. I don't remember if there's a particular
# reason that I used := when I did.
EDGE_FILES = \
	edges/dbpedia/instances.jsons edges/dbpedia/properties.jsons \
	edges/wiktionary/wiktionary_en.jsons \
	edges/wiktionary/wiktionary_ja.jsons \
	edges/wordnet/wordnet.jsons \
	edges/verbosity/verbosity.jsons \
	edges/globalmind/globalmind.jsons \
	edges/jmdict/jmdict.jsons \
	$(patsubst raw/%,edges/%, $(wildcard raw/conceptnet4/*.jsons) $(wildcard raw/conceptnet4_nadya/*.jsons)) \
	$(patsubst raw/%.txt,edges/%.jsons, $(wildcard raw/conceptnet_zh/*.txt))

# When we turn .jsons files into .csv files, we put them in the same place with
# a different extension.
CSV_FILES = $(patsubst edges/%.jsons,edges/%.csv, $(EDGE_FILES))

# You'd think there would be a better way to do this, such as the shell command
# `seq`, but I couldn't get a shell command to do the right thing here.
PIECES := 00.csv 01.csv 02.csv 03.csv 04.csv 05.csv 06.csv 07.csv 08.csv 09.csv\
          10.csv 11.csv 12.csv 13.csv 14.csv 15.csv 16.csv 17.csv 18.csv 19.csv

# SPLIT_PATTERNS is not a list of filenames; it's a list of Makefile patterns
# where we're literally sticking in the % symbol. I forget why. This should
# probably be removed.
SPLIT_PATTERNS := $(addprefix edges/split/%_, $(PIECES))

# Build other filenames in similar ways.
SPLIT_FILES = $(patsubst %,edges/split/edges_%, $(PIECES))
SORTED_FILES = $(patsubst edges/split/%,edges/sorted/%, $(SPLIT_FILES))
ASSERTION_FILES = $(patsubst edges/sorted/edges_%.csv,assertions/part_%.jsons, $(SORTED_FILES))
ASSOC_FILES = $(patsubst assertions/%.jsons,assoc/%.csv, $(ASSERTION_FILES))
COMBINED_CSVS = $(patsubst assertions/%.jsons,assertions/%.csv, $(ASSERTION_FILES))
SOLR_FILES = $(patsubst assertions/%.jsons,solr/%.json, $(ASSERTION_FILES))
DIST_FILES = $(OUTPUT_FOLDER)/$(RAW_DATA_PACKAGE) \
			 $(OUTPUT_FOLDER)/conceptnet5_csv_$(DATE).tar.bz2 \
			 $(OUTPUT_FOLDER)/conceptnet5_flat_json_$(DATE).tar.bz2 \
			 $(OUTPUT_FOLDER)/conceptnet5_solr_json_$(DATE).tar.bz2 \
			 $(OUTPUT_FOLDER)/conceptnet5_vector_space_$(DATE).tar.bz2

# By default, our goal is to build the Solr data files. (build_assoc used to
# be here, but now I think it should be run explicitly -- it's a huge memory
# hog.)
#
# A complete run might look like this:
#     make download build_solr build_assoc upload
all: build_solr
build_assoc: $(ASSOC_DIR)/u.npy
build_solr: $(SOLR_FILES)
build_assertions: $(COMBINED_CSVS)
build_splits: $(SORTED_FILES)
build_csvs: $(CSV_FILES)
build_edges: $(EDGE_FILES)

# A Makefile idiom that means "don't delete intermediate files"
.SECONDARY:

# A phony target that lets you run 'make download' to get the raw data.
download :
	curl -O $(DOWNLOAD_URL)/current/$(RAW_DATA_PACKAGE)
	tar jxvf $(RAW_DATA_PACKAGE)

# A target that lets you (well, me) run 'make upload' to put the data
# on conceptnet5.media.mit.edu.
upload : $(DIST_FILES)
	rsync -Pav $(OUTPUT_FOLDER) $(DOWNLOAD_SSH_LOC)

# Build steps
# ===========
# These rules explain how to build various files. Their dependencies
# are the source files, plus the Python code that's actually responsible
# for the building, because everything should be rebuilt if the Python
# code changes.

# Read edges from ConceptNet raw files.
edges/conceptnet4/%.jsons : raw/conceptnet4/%.jsons $(READERS)/conceptnet4.py
	@mkdir -p $$(dirname $@)
	$(PYTHON) -m conceptnet5.readers.conceptnet4 $< $@

# nadya.jp output is in the same format as ConceptNet.
edges/conceptnet4_nadya/%.jsons : raw/conceptnet4_nadya/%.jsons $(READERS)/conceptnet4.py
	@mkdir -p $$(dirname $@)
	$(PYTHON) -m conceptnet5.readers.conceptnet4 $< $@

# zh-TW data from the PTT Pet Game is in a different format, in .txt files.
edges/conceptnet_zh/%.jsons : raw/conceptnet_zh/%.txt $(READERS)/ptt_petgame.py
	@mkdir -p $$(dirname $@)
	$(PYTHON) -m conceptnet5.readers.ptt_petgame $< $@

# GlobalMind objects refer to each other, so the reader has to handle them all
# in the same process.
edges/globalmind/globalmind.jsons: raw/globalmind/*.yaml $(READERS)/globalmind.py
	@mkdir -p edges/globalmind
	$(PYTHON) -m conceptnet5.readers.globalmind raw/globalmind $@

# One day, this will be replaced by a better Wiktionary reader.
edges/wiktionary/wiktionary_en.jsons: raw/wiktionary/enwiktionary.xml $(READERS)/wiktionary_en.py
	@mkdir -p edges/wiktionary
	$(PYTHON) -m conceptnet5.readers.wiktionary_en $< $@

edges/wiktionary/wiktionary_ja.jsons: raw/wiktionary/jawiktionary.xml $(READERS)/wiktionary_ja.py
	@mkdir -p edges/wiktionary
	$(PYTHON) -m conceptnet5.readers.wiktionary_ja $< $@

# Verbosity and WordNet are also indivisible scripts; it has to be handled
# all at once, by one process.
edges/verbosity/verbosity.jsons: raw/verbosity/verbosity.txt $(READERS)/verbosity.py
	@mkdir -p edges/verbosity
	$(PYTHON) -m conceptnet5.readers.verbosity $< $@

# The WordNet script has an additional output, which goes into 'sw_map':
# a mapping of Semantic Web URLs to ConceptNet 5 nodes.
edges/wordnet/wordnet.jsons: raw/wordnet/*.ttl raw/wordnet/full/*.ttl $(READERS)/wordnet.py
	@mkdir -p edges/wordnet
	@mkdir -p sw_map
	$(PYTHON) -m conceptnet5.readers.wordnet raw/wordnet $@ sw_map/wordnet.jsons

# Read edges from DBPedia. This script also produces an sw_map.
edges/dbpedia/instances.jsons: raw/dbpedia/instance_types_en.nt $(READERS)/dbpedia.py
	@mkdir -p edges/dbpedia
	@mkdir -p sw_map
	$(PYTHON) -m conceptnet5.readers.dbpedia $< $@ sw_map/dbpedia_instances.jsons

edges/dbpedia/properties.jsons: raw/dbpedia/mappingbased_properties_en.nt $(READERS)/dbpedia.py
	@mkdir -p edges/dbpedia
	@mkdir -p sw_map
	$(PYTHON) -m conceptnet5.readers.dbpedia $< $@ sw_map/dbpedia_properties.jsons

# Read Japanese translations from JMDict.
edges/jmdict/jmdict.jsons: raw/jmdict/JMdict.xml $(READERS)/jmdict.py
	@mkdir -p edges/jmdict
	$(PYTHON) -m conceptnet5.readers.jmdict $< $@

# This rule covers building any edges/*.csv file from its corresponding
# .jsons file.
edges/%.csv: edges/%.jsons $(BUILDERS)/json_to_csv.py
	$(PYTHON) -m conceptnet5.builders.json_to_csv $< $@

# Gather all the csv files and split them into 20 pieces.
$(SPLIT_FILES): $(CSV_FILES) $(BUILDERS)/distribute_edges.py
	@mkdir -p edges/split
	cat $(CSV_FILES) | $(PYTHON) -m conceptnet5.builders.distribute_edges -o edges/split -n 20

# Make sorted, uniquified versions of the split-up edge files.
edges/sorted/%.csv: edges/split/%.csv
	@mkdir -p edges/sorted
	sort $< | uniq > $@

# An assertion may be built from multiple similar edges, where the only
# difference between them is the knowledge source. Combine edges with the same
# assertion URI into single assertions.
assertions/part_%.jsons: edges/sorted/edges_%.csv $(BUILDERS)/combine_assertions.py
	@mkdir -p assertions
	$(PYTHON) -m conceptnet5.builders.combine_assertions $< $@ -d /d/conceptnet/5/combined-sa -l /l/CC/By-SA

assertions/%.csv: assertions/%.jsons
	$(PYTHON) -m conceptnet5.builders.json_to_csv $< $@

# Convert the assertions into unlabeled associations between concepts.
assoc/%.csv: assertions/%.jsons $(BUILDERS)/json_to_assoc.py
	@mkdir -p assoc
	$(PYTHON) -m conceptnet5.builders.json_to_assoc $< $@

# Combine all associations into one file.
assoc/all.csv: $(ASSOC_FILES)
	cat $(ASSOC_FILES) > $@

# Use the external `assoc_space` package to build a dimensionality-reduced
# matrix of term-term associations.
$(ASSOC_DIR)/u.npy: assoc/all.csv
	$(PYTHON) -m assoc_space.build_conceptnet $< $(ASSOC_DIR)

# Solr's input is made of peculiarly-structured JSON files. Build those
# files from our files of multiple JSON assertions.
solr/%.json: assertions/%.jsons $(BUILDERS)/json_to_solr.py
	@mkdir -p solr
	$(PYTHON) -m conceptnet5.builders.json_to_solr $< $@

# The following rules are for building the DIST_FILES to be uploaded.
$(OUTPUT_FOLDER)/$(RAW_DATA_PACKAGE): raw/*/*
	@mkdir -p $(OUTPUT_FOLDER)
	tar jcvf $@ raw/*/*

$(OUTPUT_FOLDER)/conceptnet5_flat_json_$(DATE).tar.bz2: assertions/*.jsons
	@mkdir -p $(OUTPUT_FOLDER)
	tar jcvf $@ assertions/*.jsons

$(OUTPUT_FOLDER)/conceptnet5_solr_json_$(DATE).tar.bz2: solr/*.json
	@mkdir -p $(OUTPUT_FOLDER)
	tar jcvf $@ solr

$(OUTPUT_FOLDER)/conceptnet5_csv_$(DATE).tar.bz2: assertions/*.csv
	@mkdir -p $(OUTPUT_FOLDER)
	tar jcvf $@ assertions/*.csv

$(OUTPUT_FOLDER)/conceptnet5_vector_space_$(DATE).tar.bz2: $(ASSOC_DIR)/*
	@mkdir -p $(OUTPUT_FOLDER)
	tar jcvf $@ $(ASSOC_DIR)

