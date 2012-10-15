DATE = $$(date +%Y%m%d_%H%M%S)
CSV_FILES = */data/flat/*.csv

all_json: conceptnet4_json conceptnet4_zh_json dbpedia_json globalmind_json reverb_json verbosity_json wordnet_json wiktionary_json

conceptnet4_json: force_look
	cd conceptnet4/ ; make conceptnet4_json

conceptnet4_zh_json: force_look 
	cd conceptnet4_zh/ ; make conceptnet_zh_json

dbpedia_json: force_look
	cd dbpedia/ ; make dbpedia_json

globalmind_json: force_look
	cd globalmind/ ; make globalmind_json

reverb_json: force_look
	cd reverb/ ; make reverb_json 

verbosity_json: force_look
	cd verbosity/ ; make verbosity_json

wordnet_json: force_look
	cd wordnet/ ; make wordnet_json

wiktionary_json: force_look
	cd wiktionary/ ; make wiktionary_json


all_csv: conceptnet4_csv conceptnet4_zh_csv reverb_csv wordnet_csv verbosity_csv dbpedia_csv globalmind_csv wiktionary_csv

conceptnet4_csv: force_look
	cd conceptnet4/ ; make conceptnet4_csv

conceptnet4_zh_csv: force_look 
	cd conceptnet_zh/ ; make conceptnet_zh_csv

reverb_csv: force_look
	cd reverb/ ; make reverb_csv

wordnet_csv: force_look
	cd wordnet/ ; make wordnet_csv

verbosity_csv: force_look
	cd verbosity/ ; make verbosity_csv

dbpedia_csv: force_look
	cd dbpedia/ ; make dbpedia_csv

globalmind_csv: force_look
	cd globalmind/ ; make globalmind_csv

wiktionary_csv: force_look
	cd wiktionary/ ; make wiktionary_csv


core: $(CSV_FILES)
	python scripts/flat_assertions.py $(CSV_FILES)

tar_bz_from_json: force_look
	tar -cjf solr_json_$(DATE).tar.bz2 */data/solr/*.json core_data/solr/*.json

force_look:
	true
