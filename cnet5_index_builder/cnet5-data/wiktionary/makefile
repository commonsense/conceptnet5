JSON_DEPENDENCIES = read_wiktionary.py raw_data/enwiktionary.xml
JSON_TARGET = data/flat/*.json
CSV_TARGET = data/flat/*.csv

all: csv 

json: $(JSON_TARGET)

csv: $(CSV_TARGET)


$(JSON_TARGET): $(JSON_DEPENDENCIES)
	python read_wiktionary.py

$(CSV_TARGET): $(JSON_TARGET)
	python ../scripts/flatten_json_to_csv.py $(JSON_TARGET)

	
clean: 
	#touch is used in case folders are already empty so no error is thrown
	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*