JSON_DEPENDENCIES = read_wiktionary.py raw_data/enwiktionary.xml
CSV_DEPENDENCIES = wiktionary.json

wiktionary_json: $(WIKTIONARY_DEPENDENCIES)
	python read_wiktionary.py

wiktionary_csv: $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py $(CSV_DEPENDENCIES)
