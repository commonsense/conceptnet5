# ConceptNet-related configuration
# ================================
# $(READERS) and $(BUILDERS) specify where the scripts that take in raw
# data and build ConceptNet are located, so we know to rebuild files when
# they change.
BASE = ../conceptnet5
READERS = $(BASE)/readers
BUILDERS = $(BASE)/builders

# $(CORE) is the set of ConceptNet modules that affect every step of the
# building process. If one of these modules changes, we need to build from
# scratch.
CORE = ../conceptnet5/uri.py ../conceptnet5/nodes.py ../conceptnet5/edges.py

# When building a package to distribute, it will be marked with the current
# date.
DATE = $(shell date +%Y%m%d)
OUTPUT_FOLDER = dist/$(DATE)
DATA_SYMLINK = ~/.conceptnet5

# The URL from which to download ConceptNet files, such as the raw data files.
DOWNLOAD_URL = http://conceptnet5.media.mit.edu/downloads
RAW_DATA_PACKAGE = conceptnet5-raw-data.tar.bz2

# The hostname and path that we use to upload files, so they can be downloaded
# later.
#
# Of course this path only works if you have Media Lab credentials and write
# access to conceptnet5, so if you're distributing your own version, be sure
# to change this to a server you control.
UPLOAD_PATH = conceptnet5.media.mit.edu:/var/www/conceptnet5/downloads

# The name of the assoc_space directory to build.
ASSOC_DIR = assoc/assoc-space-5.2


# Configuration of Unix tools
# ===========================
# $(PYTHON) should point to an installation of Python 3.3 or later, with
# conceptnet5 installed as a library.
#
# If you're in an appropriate virtualenv, this will simply be 'python'.
PYTHON = python

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

# 20-way splits
# =============
# Some steps of the process can be parallelized by splitting the input into
# independent pieces. Here we create the pieces of filenames necessary to
# implement a 20-way fan-out.
#
# You'd think there would be a better way to do this, such as the shell command
# `seq`, but I couldn't get a shell command to do the right thing here.
PIECES  := 	00.csv 01.csv 02.csv 03.csv 04.csv 05.csv 06.csv 07.csv 08.csv 09.csv\
			10.csv 11.csv 12.csv 13.csv 14.csv 15.csv 16.csv 17.csv 18.csv 19.csv
JPIECES := 	00.jsons 01.jsons 02.jsons 03.jsons 04.jsons 05.jsons 06.jsons 07.jsons 08.jsons 09.jsons\
			10.jsons 11.jsons 12.jsons 13.jsons 14.jsons 15.jsons 16.jsons 17.jsons 18.jsons 19.jsons

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
	edges/wordnet/wordnet.jsons \
	edges/verbosity/verbosity.jsons \
	edges/globalmind/globalmind.jsons \
	edges/jmdict/jmdict.jsons \
	$(patsubst %,edges/wiktionary/en/wiktionary_%, $(JPIECES)) \
	$(patsubst raw/%,edges/%, $(wildcard raw/conceptnet4/*.jsons) $(wildcard raw/conceptnet4_nadya/*.jsons)) \
	$(patsubst raw/%.txt,edges/%.jsons, $(wildcard raw/conceptnet_zh/*.txt))

# When we turn .jsons files into .csv files, we put them in the same place with
# a different extension.
CSV_FILES = $(patsubst edges/%.jsons,edges/%.csv, $(EDGE_FILES))

# Build other filenames in similar ways.
SPLIT_FILES := $(patsubst %,edges/split/edges_%, $(PIECES))
SORTED_FILES = $(patsubst edges/split/%,edges/sorted/%, $(SPLIT_FILES))
ASSERTION_FILES = $(patsubst edges/sorted/edges_%.csv,assertions/part_%.jsons, $(SORTED_FILES))
ASSOC_FILES = $(patsubst assertions/%.jsons,assoc/%.csv, $(ASSERTION_FILES))
COMBINED_CSVS = $(patsubst assertions/%.jsons,assertions/%.csv, $(ASSERTION_FILES))
SOLR_FILES = $(patsubst assertions/%.jsons,solr/%.json, $(ASSERTION_FILES))
DIST_FILES = $(OUTPUT_FOLDER)/$(RAW_DATA_PACKAGE) \
			 $(OUTPUT_FOLDER)/conceptnet5_csv_$(DATE).tar.bz2 \
			 $(OUTPUT_FOLDER)/conceptnet5_flat_json_$(DATE).tar.bz2 \
			 $(OUTPUT_FOLDER)/conceptnet5_solr_json_$(DATE).tar.bz2
# skip for now: $(OUTPUT_FOLDER)/conceptnet5_vector_space_$(DATE).tar.bz2
STATS_FILES = stats/relations.txt stats/dataset_languages.txt stats/morestats.txt
SQLITE_FILE = db/conceptnet5.sqlite

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
all: build_assertions build_stats build_db
build_assoc: $(ASSOC_DIR)/u.npy
build_solr: $(SOLR_FILES)
build_db: $(SQLITE_FILE)
build_assertions: $(COMBINED_CSVS) $(ASSOC_FILES)
	# Once the assertions are built, we can benefit from the link pointing
	# from ~/.conceptnet5 to this directory.
	ln -s `pwd` $(DATA_SYMLINK)
build_splits: $(SORTED_FILES)
build_csvs: $(CSV_FILES)
build_edges: $(EDGE_FILES)
build_stats: $(STATS_FILES)


# A Makefile idiom that means "don't delete intermediate files"
.SECONDARY:

# A phony target that lets you run 'make download' to get the raw data.
download :
	$(CURL) $(DOWNLOAD_URL)/current/$(RAW_DATA_PACKAGE)
	$(TARBALL_EXTRACT) $(RAW_DATA_PACKAGE)

# A target that lets you (well, me) run 'make upload' to put the data
# on conceptnet5.media.mit.edu.
upload : $(DIST_FILES)
	$(RSYNC_UPLOAD) $(OUTPUT_FOLDER) $(UPLOAD_PATH)


# Build steps
# ===========
# These rules explain how to build various files. Their dependencies
# are the source files, plus the Python code that's actually responsible
# for the building, because everything should be rebuilt if the Python
# code changes.

# Read edges from ConceptNet raw files.
edges/conceptnet4/%.jsons: raw/conceptnet4/%.jsons $(READERS)/conceptnet4.py $(CORE)
	@mkdir -p $$(dirname $@)
	$(PYTHON) -m conceptnet5.readers.conceptnet4 $< $@

# nadya.jp output is in the same format as ConceptNet.
edges/conceptnet4_nadya/%.jsons: raw/conceptnet4_nadya/%.jsons $(READERS)/conceptnet4.py $(CORE)
	@mkdir -p $$(dirname $@)
	$(PYTHON) -m conceptnet5.readers.conceptnet4 $< $@

# zh-TW data from the PTT Pet Game is in a different format, in .txt files.
edges/conceptnet_zh/%.jsons: raw/conceptnet_zh/%.txt $(READERS)/ptt_petgame.py $(CORE)
	@mkdir -p $$(dirname $@)
	$(PYTHON) -m conceptnet5.readers.ptt_petgame $< $@

# GlobalMind objects refer to each other, so the reader has to handle them all
# in the same process.
edges/globalmind/globalmind.jsons: raw/globalmind/*.yaml $(READERS)/globalmind.py $(CORE)
	@mkdir -p edges/globalmind
	$(PYTHON) -m conceptnet5.readers.globalmind raw/globalmind $@

# The Wiktionary reader proceeds in two steps. First we extract .jsons files
# of individual sections from the huge .xml file.
#
# We can't list these 20 files as the outputs of this rule, because then it would run 20 times.
# Instead, we make a file called ".done" that gets updated after the extraction has finished.
extracted/wiktionary/en/.done: raw/wiktionary/enwiktionary.xml $(READERS)/extract_wiktionary.py
	@mkdir -p extracted/wiktionary/en
	$(PYTHON) -m conceptnet5.readers.extract_wiktionary $< extracted/wiktionary/en
	touch $@

# The Wiktionary parser is generated by a parser generator. (Hurrah for
# tautologies!) The parser code has to exist before we can use it, so we run
# its Makefile if it doesn't exist or it's out of date.
$(BASE)/wiktparse/parser.py: $(BASE)/wiktparse/rules.py $(BASE)/wiktparse/extract_ebnf.py
	cd $(BASE)/wiktparse && $(MAKE) parser.py

# The next stage of Wiktionary reading is to run the .jsons files through the
# full Wiktionary parser, which is relatively slow but can happen in parallel.
edges/wiktionary/en/%.jsons: extracted/wiktionary/en/.done $(READERS)/wiktionary.py $(BASE)/wiktparse/parser.py $(BASE)/wiktparse/rules.py $(CORE)
	@mkdir -p edges/wiktionary/en
	$(PYTHON) -m conceptnet5.readers.wiktionary -l en \
		$(patsubst edges/%,extracted/%,$@) $@

# Verbosity and WordNet are also indivisible scripts; it has to be handled
# all at once, by one process.
edges/verbosity/verbosity.jsons: raw/verbosity/verbosity.txt $(READERS)/verbosity.py $(CORE)
	@mkdir -p edges/verbosity
	$(PYTHON) -m conceptnet5.readers.verbosity $< $@

# The WordNet script has an additional output, which goes into 'sw_map':
# a mapping of Semantic Web URLs to ConceptNet 5 nodes.
edges/wordnet/wordnet.jsons: raw/wordnet/*.ttl raw/wordnet/full/*.ttl $(READERS)/wordnet.py $(CORE)
	@mkdir -p edges/wordnet
	@mkdir -p sw_map
	$(PYTHON) -m conceptnet5.readers.wordnet raw/wordnet $@ sw_map/wordnet.nt

# Read edges from DBPedia. This script also produces an sw_map.
edges/dbpedia/instances.jsons: raw/dbpedia/instance_types_en.nt $(READERS)/dbpedia.py $(CORE)
	@mkdir -p edges/dbpedia
	@mkdir -p sw_map
	$(PYTHON) -m conceptnet5.readers.dbpedia $< $@ sw_map/dbpedia_instances.nt

edges/dbpedia/properties.jsons: raw/dbpedia/mappingbased_properties_en.nt $(READERS)/dbpedia.py $(CORE)
	@mkdir -p edges/dbpedia
	@mkdir -p sw_map
	$(PYTHON) -m conceptnet5.readers.dbpedia $< $@ sw_map/dbpedia_properties.nt

# Read Japanese translations from JMDict.
edges/jmdict/jmdict.jsons: raw/jmdict/JMdict.xml $(READERS)/jmdict.py $(CORE)
	@mkdir -p edges/jmdict
	$(PYTHON) -m conceptnet5.readers.jmdict $< $@

# This rule covers building any edges/*.csv file from its corresponding
# .jsons file.
edges/%.csv: edges/%.jsons $(BUILDERS)/json_to_csv.py
	$(PYTHON) -m conceptnet5.builders.json_to_csv $< $@

# Gather all the csv files and split them into 20 pieces.
#
# As with Wiktionary above, we make an artificial file called ".done" instead
# of listing the actual outputs.
edges/split/.done: $(CSV_FILES) $(BUILDERS)/distribute_edges.py
	@mkdir -p edges/split
	cat $(CSV_FILES) | $(PYTHON) -m conceptnet5.builders.distribute_edges -o edges/split -n 20
	touch edges/split/.done

# Make sorted, uniquified versions of the split-up edge files.
#
# Because we didn't make a rule that has these split-up files as targets -- the
# previous rule has a fake target -- we need to deduce the input filenames here
# using $(patsubst).
edges/sorted/%.csv: edges/split/.done
	@mkdir -p edges/sorted
	$(SORT) $(patsubst edges/sorted/%,edges/split/%,$@) | uniq > $@

# An assertion may be built from multiple similar edges, where the only
# difference between them is the knowledge source. Combine edges with the same
# assertion URI into single assertions.
assertions/part_%.jsons: edges/sorted/edges_%.csv $(BUILDERS)/combine_assertions.py
	@mkdir -p assertions
	$(PYTHON) -m conceptnet5.builders.combine_assertions $< $@ -l /l/CC/By-SA

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

# Index the assertions in a SQLite database.
# This may become a replacement for Solr.
db/conceptnet5.sqlite: $(ASSERTION_FILES) $(BUILDERS)/index_assertions.py
	@mkdir -p db
	$(PYTHON) -m conceptnet5.builders.index_assertions assertions/ $@

# Solr's input is made of peculiarly-structured JSON files. Build those
# files from our files of multiple JSON assertions.
solr/%.json: assertions/%.jsons $(BUILDERS)/json_to_solr.py
	@mkdir -p solr
	$(PYTHON) -m conceptnet5.builders.json_to_solr $< $@

# The following rules are for building the DIST_FILES to be uploaded.
$(OUTPUT_FOLDER)/$(RAW_DATA_PACKAGE): raw/*/*
	@mkdir -p $(OUTPUT_FOLDER)
	$(TARBALL_CREATE) $@ raw/*/*

$(OUTPUT_FOLDER)/conceptnet5_flat_json_$(DATE).tar.bz2: $(ASSERTION_FILES)
	@mkdir -p $(OUTPUT_FOLDER)
	$(TARBALL_CREATE) $@ assertions/*.jsons

$(OUTPUT_FOLDER)/conceptnet5_solr_json_$(DATE).tar.bz2: $(SOLR_FILES)
	@mkdir -p $(OUTPUT_FOLDER)
	$(TARBALL_CREATE) $@ solr

$(OUTPUT_FOLDER)/conceptnet5_csv_$(DATE).tar.bz2: $(COMBINED_CSVS)
	@mkdir -p $(OUTPUT_FOLDER)
	$(TARBALL_CREATE) $@ assertions/*.csv

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
stats/relations.txt: $(COMBINED_CSVS)
	@mkdir -p stats
	$(CUT) -f 2 $(SORTED_FILES) | $(COUNT_AND_RANK) > stats/relations.txt

stats/concepts_left_datasets.txt: $(COMBINED_CSVS)
	@mkdir -p stats
	$(CUT) -f 3,9 $(SORTED_FILES) > stats/concepts_left_datasets.txt

stats/concepts_right_datasets.txt: $(COMBINED_CSVS)
	@mkdir -p stats
	$(CUT) -f 4,9 $(SORTED_FILES) > stats/concepts_right_datasets.txt

stats/concepts.txt: stats/concepts_left_datasets.txt stats/concepts_right_datasets.txt
	$(CUT) -f 1 $^ | $(COUNT_AND_RANK) > stats/concepts.txt

## This doesn't work -- concepts.txt already has counts on it, in a format that
## 'cut' doesn't like.
#stats/concepts_per_language.txt: stats/concepts.txt
#	$(CUT) -f 2 stats/concepts.txt | $(TRUNCATE_URIS) | $(COUNT_AND_RANK) > stats/concepts_per_language.txt

stats/dataset_languages.txt: stats/concepts_left_datasets.txt stats/concepts_right_datasets.txt
	cat $^ | $(TRUNCATE_URIS) | $(SORT) | $(UNIQ) -c > stats/dataset_vs_language.txt

stats/morestats.txt: $(COMBINED_CSVS)
	@mkdir -p stats
	$(CUT) -f 2,3,4,9 $(SORTED_FILES) | $(TRUNCATE_URIS) | $(COUNT_AND_RANK) > stats/morestats.txt
