JSON_DEPENDENCIES = raw_data/verbosity.txt
CSV_DEPENDENCIES = data/flat/verbosity.json

verbosity_json: $(VERBOSITY_DEPENDENCIES)
	python read_verbosity.py

verbosity_csv: $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py $(CSV_DEPENDENCIES)


clean: 
	#touch is used in case folders are already empty so no error is thrown
	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*