JSON_DEPENDENCIES = raw_data/verbosity.txt
CSV_DEPENDENCIES = data/flat/verbosity.json

verbosity_json: $(VERBOSITY_DEPENDENCIES)
	python read_verbosity.py

verbosity_csv: $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py $(CSV_DEPENDENCIES)



