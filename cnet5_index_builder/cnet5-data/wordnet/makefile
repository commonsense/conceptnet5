JSON_DEPENDENCIES = raw_data/wordnet-synset.ttl raw_data/full/wordnet-wordsensesandwords.ttl raw_data/wordnet-glossary.ttl raw_data/full/wordnet-wordsense-synset-relations.ttl raw_data/wordnet-attribute.ttl raw_data/wordnet-causes.ttl raw_data/wordnet-classifiedby.ttl raw_data/wordnet-entailment.ttl raw_data/wordnet-hyponym.ttl raw_data/wordnet-instances.ttl raw_data/wordnet-membermeronym.ttl raw_data/wordnet-partmeronym.ttl raw_data/wordnet-sameverbgroupas.ttl raw_data/wordnet-similarity.ttl raw_data/wordnet-substancemeronym.ttl raw_data/full/wordnet-antonym.ttl raw_data/full/wordnet-derivationallyrelated.ttl raw_data/full/wordnet-participleof.ttl raw_data/full/wordnet-pertainsto.ttl raw_data/full/wordnet-seealso.ttl read_wordnet.py
JSON_TARGET = data/flat/*.json
CSV_TARGET = data/flat/*.csv

all: csv

json: $(JSON_TARGET)

csv: $(CSV_TARGET)

$(JSON_TARGET): $(JSON_DEPENDENCIES)
	python read_wordnet.py

$(CSV_TARGET): $(JSON_TARGET)
	python ../scripts/flatten_json_to_csv.py $(JSON_TARGET)

clean: 
	#touch is used in case folders are already empty so no error is thrown
	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*