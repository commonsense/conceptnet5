
JSON_DEPENDENCIES = read_reverb.py raw_data/reverb_featured_triples.txt raw_data/reverb_wikipedia_tuples-1.1.txt
JSON_TARGET = data/flat/*.json
CSV_TARGET = data/flat/*.csv

all: csv

json: $(JSON_TARGET)

csv: $(CSV_TARGET) 


#used internally so you don't have to write out the entire target names
$(JSON_TARGET): $(JSON_DEPENDENCIES)
	python read_reverb.py

$(CSV_TARGET): $(JSON_TARGET)
	python ../scripts/flatten_json_to_csv.py $(JSON_TARGET)


clean: 
	#touch is used in case folders are already empty so no error is thrown
	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*
