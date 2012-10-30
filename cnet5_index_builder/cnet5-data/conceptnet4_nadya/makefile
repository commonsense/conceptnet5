JSON_DEPENDENCIES = read_conceptnet4_nadya.py
CSV_DEPENDENCIES = data/flat/nadya.jp.json
JSON_TARGET = data/flat/nadya.jp.json
CSV_TARGET = data/flat/nadya.jp.csv

conceptnet4_nadya_json: $(JSON_TARGET)

conceptnet4_nadya_csv: $(CSV_TARGET)


$(JSON_TARGET): $(JSON_DEPENDENCIES)
	python read_conceptnet4_nadya.py

$(CSV_TARGET): $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py data/flat/*.json


clean: 
	#touch is used in case folders are already empty so no error is thrown
	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*