JSON_DEPENDENCIES = read_zh.py raw_data/conceptnet_zh_api.txt raw_data/conceptnet_zh_part1.txt raw_data/conceptnet_zh_part2.txt raw_data/conceptnet_zh_part3.txt raw_data/conceptnet_zh_part4.txt raw_data/conceptnet_zh_part5.txt raw_data/conceptnet_zh_part6.txt raw_data/conceptnet_zh_part7.txt raw_data/conceptnet_zh_part8.txt raw_data/conceptnet_zh_part9.txt raw_data/conceptnet_zh_part10.txt raw_data/conceptnet_zh_part11.txt raw_data/conceptnet_zh_part12.txt
JSON_TARGET = data/flat/*.json
CSV_TARGET = data/flat/*.csv

all: csv 

json: $(JSON_TARGET)

csv: $(CSV_TARGET)


$(JSON_TARGET): $(JSON_DEPENDENCIES)
	python read_zh.py

$(CSV_TARGET): $(JSON_TARGET)
	python ../scripts/flatten_json_to_csv.py $(JSON_TARGET)


clean: 
	#touch is used in case folders are already empty so no error is thrown
	touch data/flat/abc123xzy456
	touch data/solr/abc123xyz456
	-rm data/flat/*
	-rm data/solr/*