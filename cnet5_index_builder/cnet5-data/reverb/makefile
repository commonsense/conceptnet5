
JSON_DEPENDENCIES = read_reverb.py raw_data/reverb_featured_triples.txt raw_data/reverb_wikipedia_tuples-1.1.txt
CSV_DEPENDENCIES = data/flat/*.json
JSON_TARGET = data/flat/reverb_0.json
CSV_TARGET = data/flat/reverb_0.csv

#call this to build json and csv
reverb_json: $(JSON_TARGET)

reverb_csv: $(CSV_TARGET)


#used internally so you don't have to write out the entire target names
$(JSON_TARGET): $(JSON_DEPENDENCIES)
	python read_reverb.py

$(CSV_TARGET): $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py data/flat/*.json


reverb_quick_json: $(JSON_DEPENDENCIES)
	python read_reverb.py --quick_write

clean: 
	#touch is used in case folders are already empty so no error is thrown
	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*
