JSON_DEPENDENCIES = raw_data/conceptnet_zh_api.txt raw_data/conceptnet_zh_part1.txt raw_data/conceptnet_zh_part2.txt raw_data/conceptnet_zh_part3.txt raw_data/conceptnet_zh_part4.txt raw_data/conceptnet_zh_part5.txt raw_data/conceptnet_zh_part6.txt raw_data/conceptnet_zh_part7.txt raw_data/conceptnet_zh_part8.txt raw_data/conceptnet_zh_part9.txt raw_data/conceptnet_zh_part10.txt raw_data/conceptnet_zh_part11.txt raw_data/conceptnet_zh_part12.txt
CSV_DEPENDENCIES = data/flat/*.json

conceptnet4_zh_json: $(JSON_DEPENDENCIES)
	python read_zh.py

conceptnet4_zh_csv: $(CSV_DEPENDENCIES)
	python ../scripts/flatten_json_to_csv.py data/flat/*.json

clean: 
	#touch is used in case folders are already empty so no error is thrown
	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*