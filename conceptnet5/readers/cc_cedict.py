from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.uri import Licenses
from conceptnet5.nodes import standardized_concept_uri, valid_concept_name
from conceptnet5.edges import make_edge
import re

# CC-CEDICT is a continuation of the CEDICT project started by Paul Denisowski in 1997 with the aim
# to provide a complete downloadable Chinese to English dictionary with pronunciation in pinyin
# for the Chinese characters.
#
# Creative Commons Attribution-Share Alike 3.0
# http://creativecommons.org/licenses/by-sa/3.0/
#
# Referenced works:
# CEDICT - Copyright (C) 1997, 1998 Paul Andrew Denisowski
#
# CC-CEDICT can be downloaded from:
# http://www.mdbg.net/chindict/chindict.php?page=cc-cedict
#
# Additions and corrections can be sent through:
# https://cc-cedict.org/editor/editor.php
#
# For more information about CC-CEDICT see:
# https://cc-cedict.org/wiki/
#
#! version=1
#! subversion=0
#! format=ts
#! charset=UTF-8
#! entries=115521
#! publisher=MDBG
#! license=http://creativecommons.org/licenses/by-sa/3.0/
#! date=2017-09-12T05:38:52Z
#! time=1505194732

LINE_REGEX = r'(.+)\s(.+)\[.+\]\s/(.+)/'
YEAR_REGEX = r'(.+?)\s\(.+\d.+\),'
PAREN_REGEX = r'\(.+?\)'

def handle_file(filename, output_file):
    unmatched_count = 0
    total_count = 0
    count = 0
    for line in open(filename):

        # skip the intro information
        if line.startswith('#'):
            continue

        # parse the data to extract the traditional form, simplified form and the English definition
        traditional, simplified, definitions = re.match(LINE_REGEX, line).groups()
        definitions = definitions.split('/')

        # iterate through the definitions
        for definition in definitions:

            # check if date range is mentioned. Take what comes before it.
            #
            is_matched = False

            year = re.match(YEAR_REGEX, definition)
            if year:
                candidate = year.groups()[0]
                if ',' in candidate:
                    first_part = candidate.split(',')[0]
                    #print(first_part,'==>', definition)
                    #print()
                is_matched = True
                continue


            if definition.startswith('CL:'):
                is_matched = True
                continue

            if len(definition.split()) == 1:
                is_matched = True
                continue

            if '(idiom)' in definition:
                count += 1

            # remove things like (name), check if it's one word
            if '(' in definition:
                candidate = re.sub(PAREN_REGEX, '', definition).strip()
                is_matched = True

            if ';' in definition:
                print(definition)


            if not is_matched:
                #print(definition)
                unmatched_count += 1

        total_count += len(definitions)


            #for item in definition:
            #    year = re.match(YEAR_REGEX, item)
            #     if year and 'Adorno' in item:
            #         print(year.groups()[0], '==>', item, definition)
            #         print()
            #         count += 1

    print('count', count)
    print(unmatched_count)