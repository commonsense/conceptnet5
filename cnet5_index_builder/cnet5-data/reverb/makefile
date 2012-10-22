
JSON_DEPENDENCIES = raw_data/reverb_featured_triples.txt raw_data/reverb_wikipedia_tuples-1.1.txt
CSV_DEPENDENCIES = data/flat/reverb-wp-frontpage.json

reverb_json: $(REVERB_DEPENDENCIES)
	python read_reverb.py

reverb_csv: $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py data/flat/reverb-wp-frontpage.json

clean: 
	#touch is used in case folders are already empty so no error is thrown
	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*
