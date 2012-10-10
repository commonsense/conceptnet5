
all: process_raw_data create_csvs

#run multiwriter scripts to take raw data of different formats from 
#cnet5-raw-data and place standard json files in cnet5-json
process_raw_data: force_look
	cd cnet5-data/ ; make all_json

#run flat_json_to_csv.py to fill cnet5-csv with csv's
create_csvs: force_look
	cd cnet5-data/ ; make all_csv

force_look:
	true
