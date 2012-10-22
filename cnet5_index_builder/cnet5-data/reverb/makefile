
JSON_DEPENDENCIES = raw_data/reverb_featured_triples.txt raw_data/reverb_wikipedia_tuples-1.1.txt
CSV_DEPENDENCIES = data/flat/*.json

reverb_json: $(JSON_DEPENDENCIES)
	python read_reverb.py

reverb_quick_json: $(JSON_DEPENDENCIES)
	python read_reverb.py --quick_write

reverb_csv: $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py data/flat/*.json

clean: 
	#touch is used in case folders are already empty so no error is thrown
	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*
