JSON_DEPENDENCIES = read_dbpedia.py raw_data/wikipedia.txt raw_data/mappingbased_properties_en.nt raw_data/instance_types_en.nt
CSV_DEPENDENCIES = data/flat/dbpedia.1.json
JSON_TARGET = data/flat/dbpedia.1.json
CSV_TARGET = data/flat/dbpedia.1.csv

dbpedia_json: $(JSON_TARGET)

dbpedia_csv: $(CSV_TARGET)


$(JSON_TARGET): $(JSON_DEPENDENCIES)
	python read_dbpedia.py

$(CSV_TARGET): $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py data/flat/*.json


clean: 
	#touch is used in case folders are already empty so no error is thrown
	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*