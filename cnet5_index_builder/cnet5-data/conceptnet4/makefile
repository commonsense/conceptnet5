CSV_DEPENDENCIES = data/flat/*.json

conceptnet4_json: 
	python read_conceptnet4.py

conceptnet4_csv: $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py data/flat/*.json