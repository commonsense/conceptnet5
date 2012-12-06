JSON_DEPENDENCIES = read_conceptnet4_nadya.py
JSON_TARGET = data/flat/*.json
CSV_TARGET = data/flat/*.csv



all: csv

json: $(JSON_TARGET)

csv: $(CSV_TARGET)


$(JSON_TARGET): $(JSON_DEPENDENCIES)
	export PYTHONPATH=/conceptnet5/cnet5_index_builder/cnet5-data/conceptnet4_nadya/db_config/
	python read_conceptnet4_nadya.py --quick_write

$(CSV_TARGET): $(JSON_TARGET)
	python ../scripts/flatten_json_to_csv.py $(JSON_TARGET)


clean: 
	#touch is used in case folders are already empty so no error is thrown
	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*