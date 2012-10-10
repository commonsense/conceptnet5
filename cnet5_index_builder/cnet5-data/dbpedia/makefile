JSON_DEPENDENCIES = raw_data/wikipedia.txt raw_data/mappingbased_properties_en.nt raw_data/instance_types_en.nt

CSV_DEPENDENCIES = data/flat/dbpedia.*.json


dbpedia_json: $(JSON_DEPENDENCIES)
	python read_dbpedia.py

dbpedia_csv: $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py data/flat/*.json
