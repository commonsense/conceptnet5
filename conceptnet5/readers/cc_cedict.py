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
DATE_RANGE_REGEX = r'(.+?)\s\(.+\d.+\),'
PAREN_REGEX = re.compile(r'\(.+?\)')
CHINESE_CHAR_REGEX = re.compile(r'([\u4e00-\u9fff]+[\|·]?)+')
BRACKETS_REGEX = re.compile(r'\[.+\]')
ABBREV_REGEX = re.compile(r'')


# sb, sth, remove "to" from the beginning

def remove_reference_syntax(definition):
    definition = CHINESE_CHAR_REGEX.sub('', definition)
    return BRACKETS_REGEX.sub('', definition)


def remove_additional_info(definition):
    return definition.split(',')[0]


def extract_person(match):
    """
    Example: "Pierre-Auguste Renoir (1841-1919), French impressionist painter"
    Check if a date range is mentioned in a definition. This is usually the case when a person is
    being defined. In that case, we want to only extract the name, without the date range or the
    second, CV sentence.

    Returns:
        a list of names extracted from a definition
    """
    person = match.groups()[0]
    if ',' in person: # skip the second, CV sentence
        person = remove_additional_info(person)

    person = CHINESE_CHAR_REGEX.sub('', person)
    person = BRACKETS_REGEX.sub('', person) # delete pronunciation
    person = person.split(' or ') # Take care of "Frederic Chopin or Fryderyk Franciszek Chopin"
    return person


def extract_measure_words(definition):
    """
    Example: CL:枝[zhi1],根[gen1],個|个[ge4],把[ba3]
    """
    words = definition[3:] # skip 'CL:'
    words = words.split(',')
    words = [BRACKETS_REGEX.sub('', word) for word in words] # delete the pronunciation
    related_words = []
    for word in words:
        related_words.extend(word.split('|'))
    return related_words





def handle_file(filename, output_file):
    unmatched_count = 0
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

            # Skip pronunciations
            if 'Taiwan pr.' in definition or 'also pr.' in definition:
                continue

            # Check if it's the definition of a person
            match = re.match(DATE_RANGE_REGEX, definition)
            if match:
                edge_candidate = extract_person(match)
                continue

            # Check if a name is a measure word
            if definition.startswith('CL:'):
                related_words = extract_measure_words(definition)
                continue

            # Remove clarifying information in parenthesis
            match = re.match(PAREN_REGEX, definition)

            # Capture 'variant of'
            if definition.startswith(('variant of', 'archaic version of', 'old variant of',
                                      'also written', 'abbr.')):
                continue


            # Remove 'lit.', 'fig.'
            if definition.startswith(('lit.', 'fig.')):
                definition = definition[4:]

            # Replace sb with someone
            if 'sth' in definition:
                print(definition)

            # Replace sth with something


            # TODO should I skip 'e.g.'?

            definition = PAREN_REGEX.sub('', definition)
            definition = remove_reference_syntax(definition)
            definition = remove_additional_info(definition)
            #print(definition)




                # length requirement will be the last one there, right before making an edge


            #for item in definition:
            #    year = re.match(YEAR_REGEX, item)
            #     if year and 'Adorno' in item:
            #         print(year.groups()[0], '==>', item, definition)
            #         print()
            #         count += 1
    print(count)