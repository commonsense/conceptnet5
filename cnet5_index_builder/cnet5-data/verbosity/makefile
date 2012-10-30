JSON_DEPENDENCIES = read_verbosity.py raw_data/verbosity.txt
CSV_DEPENDENCIES = data/flat/verbosity.json
JSON_TARGET = data/flat/verbosity.json
CSV_TARGET = data/flat/verbosity.csv 

verbosity_json: $(JSON_TARGET)

verbosity_csv: $(CSV_TARGET)


$(JSON_TARGET): $(JSON_DEPENDENCIES)
	python read_verbosity.py

$(CSV_TARGET): $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py $(CSV_DEPENDENCIES)


clean: 
	#touch is used in case folders are already empty so no error is thrown
	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*