CSV_DEPENDENCIES = data/flat/conceptnet4.json

conceptnet4_json: force_look
	python read_conceptnet4.py

conceptnet4_csv: $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py data/flat/*.json

force_look:
	true