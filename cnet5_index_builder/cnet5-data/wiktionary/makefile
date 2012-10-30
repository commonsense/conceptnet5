JSON_DEPENDENCIES = read_wiktionary.py raw_data/enwiktionary.xml
CSV_DEPENDENCIES = data/flat/wiktionary.json
JSON_TARGET = data/flat/wiktionary.json
CSV_TARGET = data/flat/wiktionary.csv

wiktionary_json: $(JSON_TARGET)

wiktionary_csv: $(CSV_TARGET)


$(JSON_TARGET): $(JSON_DEPENDENCIES)
	python read_wiktionary.py

$(CSV_TARGET): $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py $(CSV_DEPENDENCIES)

	
clean: 
	#touch is used in case folders are already empty so no error is thrown
	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*