JSON_DEPENDENCIES = read_conceptnet4.py
CSV_DEPENDENCIES = data/flat/conceptnet4.json
JSON_TARGET = data/flat/conceptnet4.json
CSV_TARGET = data/flat/conceptnet4.csv

conceptnet4_json: $(JSON_TARGET)

conceptnet4_csv: $(CSV_TARGET)


$(JSON_TARGET): $(JSON_DEPENDENCIES)
	python read_conceptnet4.py

$(CSV_TARGET): $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py data/flat/*.json


clean: 
	#touch is used in case folders are already empty so no error is thrown
	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*

