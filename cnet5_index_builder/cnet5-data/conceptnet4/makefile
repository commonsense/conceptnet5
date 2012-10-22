CSV_DEPENDENCIES = data/flat/conceptnet4.json

conceptnet4_json: force_look
	python read_conceptnet4.py

conceptnet4_csv: $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py data/flat/*.json

clean: 
	#touch is used in case folders are already empty so no error is thrown
	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*

force_look:
	true