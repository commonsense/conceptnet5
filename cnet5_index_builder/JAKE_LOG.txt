#Jake's 

##########################################
#build process
##########################################
1)run multiwriter scripts to take raw data of different formats from cnet5-raw-data and place standard json files in cnet5-json

2)run flat_json_to_csv.py to fill cnet5-csv with csv's

3)run flat_assertions.py to create larger json files that are compilations of the other json files

4)take json files from 1) and 3) and index them in solr

5) create tar.gz files and send to enemity so that they can be downloaded by whoever



##########################################
#Useful things
##########################################

scp from new-caledonia to the lab computer:
digitial-intuition@digitialintuition-Inspiron-620:~/ConceptNet5$ scp -r jvarley@new-caledonia:/Users/rspeer/code/conceptnet5/import/*  cnet5-raw-data/

good resource for recursive make:
http://www.makelinux.net/make3/make3-CHP-6-SECT-1



###########################################
#Work Log
###########################################

######################FROM MONDAY OCTOBER 1st
#I did the following
1) copied all off the files from new-caledonia onto this machine
2) made makefiles for raw_reverb and raw_wordnet
3) made makefile for raw files that recursively makes reverb and raw_wordnet

#next steps: 
1) finish up all of these raw_make files.  They all produce outputs left in the data folders
2) write next set of make files to process information from the data folders

######################From Friday OCTOBER 5th
#I did the following
1) made makefiles for dbpedia, globalmind, verbosity, wiktionary 
2) reorganized so that all raw data sets have data and raw_data folder
3) made make commands to create csv's for all data sources

#next steps:
1) conceptnet4 data has no makefile yet, need to make one, and figure out how to run it
2) need to figure out how to run flat_assertions.py and where I want to put those .json files
3) can probably start getting rid of some of the data_copy folders

#######################From Tuesday October 9th
#I did the following
1) started conceptnet_zh makefile, throws error though
2) got rid of data_copy folders

#next steps:
1) ask lots of questions
2) need to move ENV inside of ConceptNet5

##########################################
#Questions for Catherine/Rob
##########################################

1)how to build global mind?  I run the read_globalmind.py and:

	    raise MeCabError("`mecab` didn't start. See README.txt for details "
		metanl.japanese.MeCabError: `mecab` didn't start. See README.txt for details about installing MeCab and other Japanese NLP tools.

 but there is no readme. 

 	ANS: Need to download/setup mecab-ipadic-utf8


5) read_verbosity.py does not work

6) read_zh.py does not work.  Throws Django error:

  		raise ImproperlyConfigured("settings.DATABASES is improperly configured. "
		django.core.exceptions.ImproperlyConfigured: settings.DATABASES is improperly configured. Please supply the ENGINE value. Check settings documentation for more details.

	more info about how it builds would be helpful.  What is inside the Django DB, ConceptNet4?


7)read_conceptnet.py throws the same error.

8) What creates CORE? flat_assertions.py takes it as input to build larger .json files, but how does core get updated when something like wordnet changes? 

	ANS: Just all the csv's concatenated together
