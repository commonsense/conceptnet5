

JSON_DEPENDENCIES = raw_data/wordnet-synset.ttl raw_data/full/wordnet-wordsensesandwords.ttl raw_data/wordnet-glossary.ttl raw_data/full/wordnet-wordsense-synset-relations.ttl raw_data/wordnet-attribute.ttl raw_data/wordnet-causes.ttl raw_data/wordnet-classifiedby.ttl raw_data/wordnet-entailment.ttl raw_data/wordnet-hyponym.ttl raw_data/wordnet-instances.ttl raw_data/wordnet-membermeronym.ttl raw_data/wordnet-partmeronym.ttl raw_data/wordnet-sameverbgroupas.ttl raw_data/wordnet-similarity.ttl raw_data/wordnet-substancemeronym.ttl raw_data/full/wordnet-antonym.ttl raw_data/full/wordnet-derivationallyrelated.ttl raw_data/full/wordnet-participleof.ttl raw_data/full/wordnet-pertainsto.ttl raw_data/full/wordnet-seealso.ttl read_wordnet.py

CSV_DEPENDENCIES = data/flat/wordnet3.json


wordnet_json: $(WORDNET_DEPENDENCIES)
	python read_wordnet.py

wordnet_csv: $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py $(CSV_DEPENDENCIES)
