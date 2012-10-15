CSV_DEPENDENCIES = data/flat/*.json

conceptnet4_nadya_json: 
	python read_conceptnet4_nadya.py

conceptnet4_nadya_csv: $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py data/flat/*.json