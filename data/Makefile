PYTHON = python
READERS = readers
DATE := $$(date +%Y%m%d)
OUTPUT_FOLDER = dist/$(DATE)
DOWNLOAD_SSH_LOC = salmon.media.mit.edu:/var/www/conceptnet5/downloads
DOWNLOAD_URL = http://conceptnet5.media.mit.edu/downloads

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

CSV_FILES = $(patsubst edges/%.jsons,edges/%.csv, $(EDGE_FILES))
PIECES := 00.csv 01.csv 02.csv 03.csv 04.csv 05.csv 06.csv 07.csv 08.csv 09.csv\
          10.csv 11.csv 12.csv 13.csv 14.csv 15.csv 16.csv 17.csv 18.csv 19.csv
SPLIT_PATTERNS := $(addprefix edges/split/%_, $(PIECES))
SPLIT_FILES = $(patsubst %,edges/split/edges_%, $(PIECES))
SORTED_FILES = $(patsubst edges/split/%,edges/sorted/%, $(SPLIT_FILES))
DIST_FILES = $(OUTPUT_FOLDER)/conceptnet5-raw-data.tar.bz2

build_splits: $(SORTED_FILES)
build_csvs: $(CSV_FILES)
build_edges: $(EDGE_FILES)
distribute: $(DIST_FILES)

# Read edges from ConceptNet raw files.
edges/conceptnet4/%.jsons : raw/conceptnet4/%.jsons $(READERS)/conceptnet4.py
	mkdir -p $$(dirname $@)
	$(PYTHON) -m conceptnet5.readers.conceptnet4 < $< > $@

# nadya.jp output is in the same format.
edges/conceptnet4_nadya/%.jsons : raw/conceptnet4_nadya/%.jsons $(READERS)/conceptnet4.py
	mkdir -p $$(dirname $@)
	$(PYTHON) -m conceptnet5.readers.conceptnet4 < $< > $@

# zh-TW data from the PTT Pet Game is in a different format, in .txt files.
edges/conceptnet_zh/%.jsons : raw/conceptnet_zh/%.txt $(READERS)/ptt_petgame.py
	mkdir -p $$(dirname $@)
	$(PYTHON) -m conceptnet5.readers.ptt_petgame < $< > $@

# GlobalMind objects refer to each other, so the reader has to handle them all
# in the same process.
edges/globalmind/globalmind.jsons: raw/globalmind/*.yaml $(READERS)/globalmind.py
	mkdir -p edges/globalmind
	$(PYTHON) -m conceptnet5.readers.globalmind raw/globalmind > $@

# One day, this will be replaced by a better Wiktionary reader.
edges/wiktionary/wiktionary_en.jsons: raw/wiktionary/enwiktionary.xml $(READERS)/wiktionary_en.py
	mkdir -p edges/wiktionary
	$(PYTHON) -m conceptnet5.readers.wiktionary_en $< $@

edges/wiktionary/wiktionary_ja.jsons: raw/wiktionary/jawiktionary.xml $(READERS)/wiktionary_ja.py
	mkdir -p edges/wiktionary
	$(PYTHON) -m conceptnet5.readers.wiktionary_ja $< $@

# Verbosity and WordNet are also indivisible scripts.
edges/verbosity/verbosity.jsons: raw/verbosity/verbosity.txt $(READERS)/verbosity.py
	mkdir -p edges/verbosity
	$(PYTHON) -m conceptnet5.readers.verbosity $< $@

edges/wordnet/wordnet.jsons: raw/wordnet/*.ttl raw/wordnet/full/*.ttl $(READERS)/wordnet.py
	mkdir -p edges/wordnet
	mkdir -p sw_map
	$(PYTHON) -m conceptnet5.readers.wordnet raw/wordnet $@ sw_map/wordnet.jsons

edges/dbpedia/instances.jsons: raw/dbpedia/instance_types_en.nt $(READERS)/dbpedia.py
	mkdir -p edges/dbpedia
	$(PYTHON) -m conceptnet5.readers.dbpedia $< $@ sw_map/dbpedia_instances.jsons

edges/dbpedia/properties.jsons: raw/dbpedia/mappingbased_properties_en.nt $(READERS)/dbpedia.py
	mkdir -p edges/dbpedia
	$(PYTHON) -m conceptnet5.readers.dbpedia $< $@ sw_map/dbpedia_properties.jsons

edges/jmdict/jmdict.jsons: raw/jmdict/JMdict.xml $(READERS)/jmdict.py
	mkdir -p edges/jmdict
	$(PYTHON) -m conceptnet5.readers.jmdict $< $@

edges/%.csv: edges/%.jsons
	$(PYTHON) -m conceptnet5.builders.json_to_csv < $< > $@

$(SPLIT_PATTERNS): $(CSV_FILES)
	mkdir -p edges/split
	cat $(CSV_FILES) | $(PYTHON) -m conceptnet5.builders.distribute_edges -o edges/split -n 20

edges/sorted/%.csv: edges/split/%.csv
	mkdir -p edges/sorted
	sort $< | uniq > $@

$(OUTPUT_FOLDER)/conceptnet5-raw-data.tar.bz2: raw/*/*
	mkdir -p $(OUTPUT_FOLDER)
	tar jcvf $(OUTPUT_FOLDER)/conceptnet5-raw-data.tar.bz2 raw/

