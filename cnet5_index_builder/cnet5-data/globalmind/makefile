JSON_DEPENDENCIES = read_globalmind.py raw_data/GMUser.yaml raw_data/GMFrame.yaml raw_data/GMAssertion.yaml raw_data/GMTranslation.yaml
CSV_DEPENDENCIES = data/flat/globalmind.json
JSON_TARGET = data/flat/globalmind.json
CSV_TARGET = data/flat/globalmind.csv

globalmind_json: $(JSON_TARGET)

globalmind_csv: $(CSV_TARGET)


$(JSON_TARGET): $(JSON_DEPENDENCIES)
	python read_globalmind.py

$(CSV_TARGET): $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py data/flat/globalmind.json


clean: 
	#touch is used in case folders are already empty so no error is thrown
	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*