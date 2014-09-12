# ConceptNet-related configuration
# ================================
VERSION = 5.3

# $(PYTHON) should point to an installation of Python 3.3 or later, with
# conceptnet5 installed as a library.
#
# If you're in an appropriate virtualenv, this will be 'python3' or simply
# 'python'.
PYTHON = python3

# $(DATA) is where the data will be built. It should be on a filesystem with
# lots of available space.
#
# Relative paths under this directory are okay, but don't use components that
# will get normalized away, such as "." and "..", because they'll break the
# rules that figure out what needs to be built from what.
DATA = data
DATA_ABSOLUTE_PATH = $(shell readlink -f $(DATA))

# $(READERS) and $(BUILDERS) specify where the scripts that take in raw
# data and build ConceptNet are located, so we know to rebuild files when
# they change.
BASE := $(shell $(PYTHON) -m conceptnet5.util.whereami)
READERS = $(BASE)/readers
BUILDERS = $(BASE)/builders

# $(CORE) is the set of ConceptNet modules that affect every step of the
# building process. If one of these modules changes, we need to build from
# scratch.
CORE = $(BASE)/uri.py $(BASE)/nodes.py $(BASE)/edges.py

# When building a package to distribute, it will be marked with the current
# date.
DATE = $(shell date +%Y%m%d)
OUTPUT_FOLDER = $(DATA)/dist/$(DATE)
DATA_SYMLINK = ~/.conceptnet5

# The URL from which to download ConceptNet files, such as the raw data files.
DOWNLOAD_URL = http://conceptnet5.media.mit.edu/downloads
RAW_DATA_PACKAGE = conceptnet5_db.tar.bz2
RAW_DATA_PACKAGE = conceptnet5-raw-data.tar.bz2

# The hostname and path that we use to upload files, so they can be downloaded
# later.
#
# Of course this path only works if you have Media Lab credentials and write
# access to conceptnet5, so if you're distributing your own version, be sure
# to change this to a server you control.
UPLOAD_PATH = conceptnet5.media.mit.edu:/var/www/conceptnet5/downloads

# The name of the assoc_space directory to build.
ASSOC_DIR = $(DATA)/assoc/assoc-space-$(VERSION)

# Configuration of Unix tools
# ===========================
# Commands for downloading and uploading data
CURL_DOWNLOAD = curl -O
RSYNC_UPLOAD = rsync -Pavz

# We use recursive make sparingly, but we still use it.
MAKE = make

# Commands for working with .tar.bz2 files
TARBALL_CREATE = tar jcvf
TARBALL_EXTRACT = tar jxvf

# 'sort' and 'uniq' are very useful Unix utilities for working with text.
# By default, they'll do something crazy and locale-specific when given
# Unicode text. This will fail utterly when the text really is in more
# than one language.
#
# LC_ALL=C tells them to ignore Unicode and treat it as arbitrary bytes.
# The result is both faster and more consistent than what locales do.
#
# The COUNT_AND_RANK pipeline is used to count occurrences of things:
#     'sort | uniq -c': group identical strings, and count their occurrences
#     'sort -nbr': show the results in descending order by count
SORT = LC_ALL=C sort
UNIQ = LC_ALL=C uniq
COUNT_AND_RANK = $(SORT) | $(UNIQ) -c | $(SORT) -nbr
CUT = cut

# This is a mini-script that takes in tab-separated data, and truncates
# all URIs it sees to the first two components. For example,
# '/c/en/toast' becomes '/c/en'. This is useful for collecting aggregate
# statistics.
TRUNCATE_URIS = sed -r 's:((/[^/\t]+){2})[^\t]*:\1:g'
#
# That could have been done in Python in a way that doesn't look like
# a monkey banged on the keyboard, I know. But, as a way of turning text
# into other text, sed is convenient and *fast*.
#
# The overall sed command is a regular expression substitution, of the
# form s:PATTERN:REPLACEMENT:g. (The more familiar form of this is
# s/PATTERN/REPLACEMENT/g, but we need to use a lot of slashes in the
# pattern.)
#
# The "-r" switch means that symbols such as parentheses automatically have
# their regular expression meaning.
#
# The expression (/[^/\t]+) matches a URI component such as /en -- that is,
# a slash, followed by some characters that aren't slashes or tabs.
#
# We ask for this expression to be repeated twice, with {2}, and capture what
# it matches using the parenthesized expression ((/[^/\t]+){2}).
#
# We then consume everything afterward that isn't a tab character: [^\t]*
#
# The replacement expression is simply \1 -- the part of the URI that matched
# the twice-repeated group.

# 20-way and 8-way splits
# =======================
# Some steps of the process can be parallelized by splitting the input into
# independent pieces. Here we create the pieces of filenames necessary to
# implement a 20-way fan-out.
#
# You'd think there would be a better way to do this, such as the shell command
# `seq`, but I couldn't get a shell command to do the right thing here.
MPIECES := 	00.msgpack 01.msgpack 02.msgpack 03.msgpack 04.msgpack 05.msgpack 06.msgpack 07.msgpack 08.msgpack 09.msgpack\
			10.msgpack 11.msgpack 12.msgpack 13.msgpack 14.msgpack 15.msgpack 16.msgpack 17.msgpack 18.msgpack 19.msgpack

# Eventually we distribute edges into 8 pieces.
PIECES_OF_EIGHT := 00.csv 01.csv 02.csv 03.csv 04.csv 05.csv 06.csv 07.csv

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
EDGE_FILES := \
	$(DATA)/edges/dbpedia/instances.msgpack $(DATA)/edges/dbpedia/properties.msgpack \
	$(DATA)/edges/wordnet/wordnet.msgpack \
	$(DATA)/edges/verbosity/verbosity.msgpack \
	$(DATA)/edges/globalmind/globalmind.msgpack \
	$(DATA)/edges/umbel/umbel.msgpack \
	$(DATA)/edges/jmdict/jmdict.msgpack \
	$(patsubst %,$(DATA)/edges/wiktionary/en/wiktionary_%, $(MPIECES)) \
	$(patsubst %,$(DATA)/edges/wiktionary/de/wiktionary_%, $(MPIECES)) \
	$(patsubst $(DATA)/raw/%.jsons,$(DATA)/edges/%.msgpack, $(wildcard $(DATA)/raw/conceptnet4/*.jsons) $(wildcard $(DATA)/raw/conceptnet4_nadya/*.jsons)) \
	$(patsubst $(DATA)/raw/%.txt,$(DATA)/edges/%.msgpack, $(wildcard $(DATA)/raw/conceptnet_zh/*.txt))

# When we turn .msgpack files into .csv files, we put them in the same place with
# a different extension.
CSV_FILES = $(patsubst $(DATA)/edges/%.msgpack,$(DATA)/edges/%.csv, $(EDGE_FILES))

# Build other filenames in similar ways.
SPLIT_FILES := $(patsubst %,$(DATA)/edges/split/edges_%, $(PIECES_OF_EIGHT))
SORTED_FILES := $(patsubst $(DATA)/edges/split/%,$(DATA)/edges/sorted/%, $(SPLIT_FILES))
ASSERTION_FILES := $(patsubst $(DATA)/edges/sorted/edges_%.csv,$(DATA)/assertions/part_%.msgpack, $(SORTED_FILES))
ASSERTION_JSONS := $(patsubst $(DATA)/assertions/%.msgpack,$(DATA)/assertions/%.jsons, $(ASSERTION_FILES))
ASSOC_FILES := $(patsubst $(DATA)/assertions/%.msgpack,$(DATA)/assoc/%.csv, $(ASSERTION_FILES))
ASSOC_SUBSPACES := $(patsubst $(DATA)/assoc/%.csv,$(DATA)/assoc/subspaces/%/u.npy, $(ASSOC_FILES))
COMBINED_CSVS := $(patsubst $(DATA)/assertions/%.msgpack,$(DATA)/assertions/%.csv, $(ASSERTION_FILES))
DIST_FILES := $(OUTPUT_FOLDER)/$(RAW_DATA_PACKAGE) \
			  $(OUTPUT_FOLDER)/conceptnet5_csv_$(DATE).tar.bz2 \
			  $(OUTPUT_FOLDER)/conceptnet5_flat_json_$(DATE).tar.bz2 \
			  $(OUTPUT_FOLDER)/conceptnet5_db.tar.bz2
# skip for now: $(OUTPUT_FOLDER)/conceptnet5_vector_space_$(DATE).tar.bz2
STATS_FILES = $(DATA)/stats/relations.txt $(DATA)/stats/dataset_vs_language.txt $(DATA)/stats/morestats.txt
DB_DIR = $(DATA)/db
SQLITE_FILE_BASE = $(DB_DIR)/assertions.db

# High-level build tasks
# ======================
# By default, our goal is to build the SQLite data, the aggregate
# statistics, and everything they depend on.
#
# The build_assoc step is not run by default, because it's a huge memory
# hog.
#
# A complete run, including all steps, might look like this:
#     make download all build_assoc upload
all: build_assertions build_stats build_cc_by build_db build_dist
parsers: $(BASE)/wiktparse/en_parser.py $(BASE)/wiktparse/de_parser.py
build_assoc_subspaces: $(ASSOC_SUBSPACES)
build_assoc: $(ASSOC_DIR)/u.npy
build_db: $(DB_DIR)/.done
build_splits: $(SORTED_FILES)
build_csvs: $(CSV_FILES)
build_edges: $(EDGE_FILES)
build_stats: $(STATS_FILES)
build_dist: $(DIST_FILES)
build_cc_by: $(DATA)/edges/cc_by_edges.csv

# Once the assertions are built, we can benefit from the link pointing
# from ~/.conceptnet5 to this directory.
build_assertions: $(COMBINED_CSVS) $(ASSOC_FILES)
	if [ ! -e $(DATA_SYMLINK) ]; then ln -s $(DATA_ABSOLUTE_PATH) $(DATA_SYMLINK); fi

# Remove everything except raw data and dist/
clean:
	rm -rf $(DATA)/assertions $(DATA)/edges $(DATA)/db $(DATA)/extracted $(DATA)/sw_map

# A Makefile idiom that means "don't delete intermediate files"
.SECONDARY:

# A phony target that lets you run 'make download' to get the raw data.
download:
	@mkdir -p $(DATA)
	cd $(DATA) && $(CURL_DOWNLOAD) $(DOWNLOAD_URL)/current/$(RAW_DATA_PACKAGE)
	cd $(DATA) && $(TARBALL_EXTRACT) $(RAW_DATA_PACKAGE)

# This rule lets you skip most of the build steps.
download_db:
	@mkdir -p $(DATA)
	cd $(DATA) && $(CURL_DOWNLOAD) $(DOWNLOAD_URL)/current/$(DB_PACKAGE)
	cd $(DATA) && $(TARBALL_EXTRACT) $(DB_PACKAGE)

# A target that lets you (well, me) run 'make upload' to put the data
# on conceptnet5.media.mit.edu.
upload: $(DIST_FILES)
	$(RSYNC_UPLOAD) $(OUTPUT_FOLDER) $(UPLOAD_PATH)


# Build steps
# ===========
# These rules explain how to build various files. Their dependencies
# are the source files, plus the Python code that's actually responsible
# for the building, because everything should be rebuilt if the Python
# code changes.

# Read edges from ConceptNet raw files.
$(DATA)/edges/conceptnet4/%.msgpack: $(DATA)/raw/conceptnet4/%.jsons $(READERS)/conceptnet4.py $(CORE)
	@mkdir -p $$(dirname $@)
	$(PYTHON) -m conceptnet5.readers.conceptnet4 $< $@

# nadya.jp output is in the same format as ConceptNet.
$(DATA)/edges/conceptnet4_nadya/%.msgpack: $(DATA)/raw/conceptnet4_nadya/%.jsons $(READERS)/conceptnet4.py $(CORE)
	@mkdir -p $$(dirname $@)
	$(PYTHON) -m conceptnet5.readers.conceptnet4 $< $@

# zh-TW data from the PTT Pet Game is in a different format, in .txt files.
$(DATA)/edges/conceptnet_zh/%.msgpack: $(DATA)/raw/conceptnet_zh/%.txt $(READERS)/ptt_petgame.py $(CORE)
	@mkdir -p $$(dirname $@)
	$(PYTHON) -m conceptnet5.readers.ptt_petgame $< $@

# GlobalMind objects refer to each other, so the reader has to handle them all
# in the same process.
$(DATA)/edges/globalmind/globalmind.msgpack: $(DATA)/raw/globalmind/*.yaml $(READERS)/globalmind.py $(CORE)
	@mkdir -p $(DATA)/edges/globalmind
	$(PYTHON) -m conceptnet5.readers.globalmind $(DATA)/raw/globalmind $@

# The Wiktionary reader proceeds in two steps. First we extract .msgpack files
# of individual sections from the huge .xml file.
#
# We can't list these 20 files as the outputs of this rule, because then it would run 20 times.
# Instead, we make a file called ".done" that gets updated after the extraction has finished.
$(DATA)/extracted/wiktionary/en/.done: $(DATA)/raw/wiktionary/enwiktionary.xml $(READERS)/extract_wiktionary.py
	@mkdir -p $(DATA)/extracted/wiktionary/en
	$(PYTHON) -m conceptnet5.readers.extract_wiktionary $< $(DATA)/extracted/wiktionary/en -l en
	touch $@

$(DATA)/extracted/wiktionary/de/.done: $(DATA)/raw/wiktionary/dewiktionary.xml $(READERS)/extract_wiktionary.py
	@mkdir -p $(DATA)/extracted/wiktionary/de
	$(PYTHON) -m conceptnet5.readers.extract_wiktionary $< $(DATA)/extracted/wiktionary/de -l de
	touch $@

# The Wiktionary parser is generated by a parser generator. (Hurrah for
# tautologies!) The parser code has to exist before we can use it, so we run
# its Makefile if it doesn't exist or it's out of date.
$(BASE)/wiktparse/en_parser.py: $(BASE)/wiktparse/rules.py $(BASE)/wiktparse/extract_ebnf.py
	cd $(BASE)/wiktparse && $(MAKE) en_parser.py

$(BASE)/wiktparse/de_parser.py: $(BASE)/wiktparse/rules.py $(BASE)/wiktparse/extract_ebnf.py
	cd $(BASE)/wiktparse && $(MAKE) de_parser.py

# The next stage of Wiktionary reading is to run the .msgpack files through the
# full Wiktionary parser, which is relatively slow but can happen in parallel.
$(DATA)/edges/wiktionary/en/%.msgpack: $(DATA)/extracted/wiktionary/en/.done $(READERS)/wiktionary.py $(BASE)/wiktparse/en_parser.py $(BASE)/wiktparse/rules.py $(CORE)
	@mkdir -p $(DATA)/edges/wiktionary/en
	$(PYTHON) -m conceptnet5.readers.wiktionary -l en \
		$(patsubst $(DATA)/edges/%,$(DATA)/extracted/%,$@) $@

$(DATA)/edges/wiktionary/de/%.msgpack: $(DATA)/extracted/wiktionary/de/.done $(READERS)/wiktionary.py $(BASE)/wiktparse/de_parser.py $(BASE)/wiktparse/rules.py $(CORE)
	@mkdir -p $(DATA)/edges/wiktionary/de
	$(PYTHON) -m conceptnet5.readers.wiktionary -l de \
		$(patsubst $(DATA)/edges/%,$(DATA)/extracted/%,$@) $@

# Verbosity and WordNet are also indivisible scripts; it has to be handled
# all at once, by one process.
$(DATA)/edges/verbosity/verbosity.msgpack: $(DATA)/raw/verbosity/verbosity.txt $(READERS)/verbosity.py $(CORE)
	@mkdir -p $(DATA)/edges/verbosity
	$(PYTHON) -m conceptnet5.readers.verbosity $< $@

# The WordNet script has an additional output, which goes into 'sw_map':
# a mapping of Semantic Web URLs to ConceptNet 5 nodes.
$(DATA)/edges/wordnet/wordnet.msgpack: $(DATA)/raw/wordnet/*.ttl $(DATA)/raw/wordnet/full/*.ttl $(READERS)/wordnet.py $(CORE)
	@mkdir -p $(DATA)/edges/wordnet
	@mkdir -p $(DATA)/sw_map
	$(PYTHON) -m conceptnet5.readers.wordnet $(DATA)/raw/wordnet $@ $(DATA)/sw_map/wordnet.nt

# Read edges from DBPedia. This script also produces an sw_map.
$(DATA)/edges/dbpedia/instances.msgpack: $(DATA)/raw/dbpedia/instance_types_en.nt $(READERS)/dbpedia.py $(CORE)
	@mkdir -p $(DATA)/edges/dbpedia
	@mkdir -p $(DATA)/sw_map
	$(PYTHON) -m conceptnet5.readers.dbpedia $< $@ $(DATA)/sw_map/dbpedia_instances.nt

$(DATA)/edges/dbpedia/properties.msgpack: $(DATA)/raw/dbpedia/mappingbased_properties_en.nt $(READERS)/dbpedia.py $(CORE)
	@mkdir -p $(DATA)/edges/dbpedia
	@mkdir -p $(DATA)/sw_map
	$(PYTHON) -m conceptnet5.readers.dbpedia $< $@ $(DATA)/sw_map/dbpedia_properties.nt

$(DATA)/edges/umbel/umbel.msgpack: $(DATA)/raw/umbel/umbel.nt $(DATA)/raw/umbel/umbel_links.nt $(READERS)/umbel.py $(READERS)/dbpedia.py $(CORE)
	@mkdir -p $(DATA)/edges/umbel
	@mkdir -p $(DATA)/sw_map
	$(PYTHON) -m conceptnet5.readers.umbel $(DATA)/raw/umbel $@ $(DATA)/sw_map/umbel.nt

# Read Japanese translations from JMDict.
$(DATA)/edges/jmdict/jmdict.msgpack: $(DATA)/raw/jmdict/JMdict.xml $(READERS)/jmdict.py $(CORE)
	@mkdir -p $(DATA)/edges/jmdict
	$(PYTHON) -m conceptnet5.readers.jmdict $< $@

# This rule covers building any edges/*.csv file from its corresponding
# .msgpack file.
$(DATA)/edges/%.csv: $(DATA)/edges/%.msgpack $(BUILDERS)/msgpack_to_csv.py
	$(PYTHON) -m conceptnet5.builders.msgpack_to_csv $< $@

# Make the subset of the edges available that can be reused under the CC-By
# license (as opposed to the majority of them, available under CC-By-SA).
$(DATA)/edges/cc_by_edges.csv: $(SORTED_FILES)
	cat $(SORTED_FILES) | grep -E "/d/(conceptnet|globalmind|umbel|verbosity|wordnet)" > $@

# Gather all the csv files and split them into 20 pieces.
#
# As with Wiktionary above, we make an artificial file called ".done" instead
# of listing the actual outputs.
$(DATA)/edges/split/.done: $(CSV_FILES) $(BUILDERS)/distribute_edges.py
	@mkdir -p $(DATA)/edges/split
	cat $(CSV_FILES) | $(PYTHON) -m conceptnet5.builders.distribute_edges -o $(DATA)/edges/split -n 8
	touch $(DATA)/edges/split/.done

# Make sorted, uniquified versions of the split-up edge files.
#
# Because we didn't make a rule that has these split-up files as targets -- the
# previous rule has a fake target -- we need to deduce the input filenames here
# using $(patsubst).
$(DATA)/edges/sorted/%.csv: $(DATA)/edges/split/.done
	@mkdir -p $(DATA)/edges/sorted
	$(SORT) $(patsubst $(DATA)/edges/sorted/%,$(DATA)/edges/split/%,$@) | uniq > $@

# An assertion may be built from multiple similar edges, where the only
# difference between them is the knowledge source. Combine edges with the same
# assertion URI into single assertions.
$(DATA)/assertions/part_%.msgpack: $(DATA)/edges/sorted/edges_%.csv $(BUILDERS)/combine_assertions.py
	@mkdir -p $(DATA)/assertions
	$(PYTHON) -m conceptnet5.builders.combine_assertions $< $@ -l /l/CC/By-SA

$(DATA)/assertions/%.csv: $(DATA)/assertions/%.msgpack
	$(PYTHON) -m conceptnet5.builders.msgpack_to_csv $< $@

# Convert the assertions into unlabeled associations between concepts.
$(DATA)/assoc/%.csv: $(DATA)/assertions/%.msgpack $(BUILDERS)/msgpack_to_assoc.py
	@mkdir -p $(DATA)/assoc
	$(PYTHON) -m conceptnet5.builders.msgpack_to_assoc $< $@

# Build vector spaces of associations, using the 'assoc-space' module.
$(DATA)/assoc/subspaces/%/u.npy: $(DATA)/assoc/%.csv $(BUILDERS)/assoc_to_vector_space.py
	@mkdir -p $(DATA)/assoc/subspaces
	$(PYTHON) -m conceptnet5.builders.assoc_to_vector_space $< $@

# Combine all associations into one file.
$(ASSOC_DIR)/u.npy: $(ASSOC_SUBSPACES)
	python -m conceptnet5.builders.merge_vector_spaces $(DATA)/assoc/subspaces
	rm -rf $(ASSOC_DIR)
	mv $(DATA)/assoc/subspaces/merged_complete $(ASSOC_DIR)

# Index the assertions in a SQLite database.
$(DB_DIR)/.done: $(ASSERTION_FILES) $(BUILDERS)/index_assertions.py
	@mkdir -p $(DB_DIR)
	$(PYTHON) -m conceptnet5.builders.index_assertions $(DATA)/assertions/ $(SQLITE_FILE_BASE) --input-shards 8
	touch $(DB_DIR)/.done


# Distribution
# ============
# The following rules are for building the DIST_FILES to be uploaded.
$(OUTPUT_FOLDER)/$(RAW_DATA_PACKAGE): $(DATA)/raw/*/*
	@mkdir -p $(OUTPUT_FOLDER)
	$(TARBALL_CREATE) $@ $(DATA)/raw/*/*

$(DATA)/assertions/%.jsons: $(DATA)/assertions/%.msgpack
	python -m conceptnet5.builders.msgpack_to_json $< $@

$(OUTPUT_FOLDER)/conceptnet5_flat_json_$(DATE).tar.bz2: $(ASSERTION_JSONS)
	@mkdir -p $(OUTPUT_FOLDER)
	$(TARBALL_CREATE) $@ $(DATA)/assertions/*.jsons

$(OUTPUT_FOLDER)/conceptnet5_flat_msgpack_$(DATE).tar.bz2: $(ASSERTION_JSONS)
	@mkdir -p $(OUTPUT_FOLDER)
	$(TARBALL_CREATE) $@ $(DATA)/assertions/*.msgpack

$(OUTPUT_FOLDER)/conceptnet5_db.tar.bz2: $(DB_DIR)/.done $(ASSERTION_FILES)
	@mkdir -p $(OUTPUT_FOLDER)
	$(TARBALL_CREATE) $@ $(DB_DIR) $(ASSERTION_FILES)

$(OUTPUT_FOLDER)/conceptnet5_csv_$(DATE).tar.bz2: $(COMBINED_CSVS)
	@mkdir -p $(OUTPUT_FOLDER)
	$(TARBALL_CREATE) $@ $(DATA)/assertions/*.csv

$(OUTPUT_FOLDER)/conceptnet5_vector_space_$(DATE).tar.bz2: $(ASSOC_DIR)/*
	@mkdir -p $(OUTPUT_FOLDER)
	$(TARBALL_CREATE) $@ $(ASSOC_DIR)


# Statistics
# ==========
# These commands build aggregate statistics from the data, which are helpful
# for understanding what kinds of data are in ConceptNet.
#
# Here's what happens in the pipeline that counts occurrences of different
# relations:
#
#     1. 'cut -f 2' takes only text in the second column of all input files.
#     2. 'sort | uniq -c' groups identical strings, and counts their occurrences.
#     3. 'sort -nbr' lists the results in descending order by count.
#
# Steps 2 and 3 appear repeatedly in many of these build steps, so they've been
# grouped into the expression $(COUNT_AND_RANK).
$(DATA)/stats/relations.txt: $(COMBINED_CSVS)
	@mkdir -p $(DATA)/stats
	$(CUT) -f 2 $(SORTED_FILES) | $(COUNT_AND_RANK) > $(DATA)/stats/relations.txt

$(DATA)/stats/concepts_left_datasets.txt: $(COMBINED_CSVS)
	@mkdir -p $(DATA)/stats
	$(CUT) -f 3,9 $(SORTED_FILES) > $(DATA)/stats/concepts_left_datasets.txt

$(DATA)/stats/concepts_right_datasets.txt: $(COMBINED_CSVS)
	@mkdir -p $(DATA)/stats
	$(CUT) -f 4,9 $(SORTED_FILES) > $(DATA)/stats/concepts_right_datasets.txt

$(DATA)/stats/concepts.txt: $(DATA)/stats/concepts_left_datasets.txt $(DATA)/stats/concepts_right_datasets.txt
	$(CUT) -f 1 $^ | $(COUNT_AND_RANK) > $(DATA)/stats/concepts.txt

## This doesn't work -- concepts.txt already has counts on it, in a format that
## 'cut' doesn't like.
#$(DATA)/stats/concepts_per_language.txt: $(DATA)/stats/concepts.txt
#	$(CUT) -f 2 $(DATA)/stats/concepts.txt | $(TRUNCATE_URIS) | $(COUNT_AND_RANK) > $(DATA)/stats/concepts_per_language.txt

$(DATA)/stats/dataset_vs_language.txt: $(DATA)/stats/concepts_left_datasets.txt $(DATA)/stats/concepts_right_datasets.txt
	cat $^ | $(TRUNCATE_URIS) | $(SORT) | $(UNIQ) -c > $(DATA)/stats/dataset_vs_language.txt

$(DATA)/stats/morestats.txt: $(COMBINED_CSVS)
	@mkdir -p $(DATA)/stats
	$(CUT) -f 2,3,4,9 $(SORTED_FILES) | $(TRUNCATE_URIS) | $(COUNT_AND_RANK) > $(DATA)/stats/morestats.txt
