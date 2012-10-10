#this file will take all of the raw data from sources such 
#as cnet4 and reverb and create standard json files in cnet5-json

all_json: reverb_json wordnet_json verbosity_json dbpedia_json globalmind_json wiktionary_json

reverb_json: force_look
	cd reverb/ ; make reverb_json 

wordnet_json: force_look
	cd wordnet/ ; make wordnet_json

verbosity_json: force_look
	cd verbosity/ ; make verbosity_json

dbpedia_json: force_look
	cd dbpedia/ ; make dbpedia_json

globalmind_json: force_look
	cd globalmind/ ; make globalmind_json

wiktionary_json: force_look
	cd wiktionary/ ; make wiktionary_json


all_csv: reverb_csv wordnet_csv verbosity_csv dbpedia_csv globalmind_csv wiktionary_csv

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

force_look:
	true
