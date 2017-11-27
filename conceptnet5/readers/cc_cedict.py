"""
CC-CEDICT is a continuation of the CEDICT project started by Paul Denisowski in 1997 with the aim
to provide a complete downloadable Chinese to English dictionary with pronunciation in pinyin
for the Chinese characters.

Creative Commons Attribution-Share Alike 3.0
http://creativecommons.org/licenses/by-sa/3.0/

Referenced works:
CEDICT - Copyright (C) 1997, 1998 Paul Andrew Denisowski

CC-CEDICT can be downloaded from:
http://www.mdbg.net/chindict/chindict.php?page=cc-cedict
"""

import gzip
import re

import regex

from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.nodes import standardized_concept_uri
from conceptnet5.uri import Licenses

DATASET = '/d/cc_cedict'
LICENSE = Licenses.cc_sharealike
SOURCE = [{'contributor': '/s/resource/cc_cedict/2017-10'}]

LINE_REGEX = re.compile(r'(.+)\s(.+)\[.+\]\s/(.+)/')  # separate traditional and simplified words
DATE_RANGE_REGEX = re.compile(r'(.+?)\s\(.+\d.+\),')  # date range
PAREN_REGEX = re.compile(r'\(.+?\)')  # parenthesis
HAN_CHAR_REGEX = regex.compile('([\p{IsIdeo}]+[\|·]?)+') # Han characters
BRACKETS_REGEX = re.compile(r'\[.+?\]')  # pronunciation
VARIANT_REGEX = re.compile(r'(see( also)?|(old |Japanese )?variant of|archaic version of|also '
                           r'written|same as)\s')
LIT_FIG_REGEX = re.compile(r'(\b|\s)(fig|lit).\s')
ABBR_REGEX = re.compile(r'(\b|\s)abbr. (to|of|for)')


def remove_reference_syntax(definition):
    """
    Definitions in English may contain references to Chinese words. The reference syntax contains
    vertical bar-separated Han characters as well as a pronunciation enclosed in brackets,
    as in "Jiajiang county in Leshan 樂山|乐山[Le4 shan1]".

    Remove the reference syntax.
    """
    definition = HAN_CHAR_REGEX.sub('', definition)
    return BRACKETS_REGEX.sub('', definition)


def remove_additional_info(definition):
    """
    Remove the second sentence of the definition
    """
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
    if ',' in person:
        person = remove_additional_info(person)  # skip the second sentence

    person = HAN_CHAR_REGEX.sub('', person)
    person = BRACKETS_REGEX.sub('', person) # delete pronunciation
    person = person.split(' or ') # Take care of "Frederic Chopin or Fryderyk Franciszek Chopin"
    return person


def extract_measure_words(definition):
    """
    Example: "CL:枝[zhi1],根[gen1],個|个[ge4],把[ba3]"
    """
    words = definition[3:]  # skip 'CL:'
    words = words.split(',')
    words = [BRACKETS_REGEX.sub('', word) for word in words]
    measure_words = []
    for word in words:
        measure_words.extend(word.split('|'))
    return measure_words


def extract_variants(definition):
    """
    Extract variants of character
    Example: "variant of 齊大非偶|齐大非偶[qi2 da4 fei1 ou3]"
    """
    variants = VARIANT_REGEX.sub('', definition)
    variants = BRACKETS_REGEX.sub('', variants)
    variants = variants.split('|')
    return variants


def extract_abbreviations(definition):
    """
    abbr.for Luxembourg 盧森堡 | 卢森堡[Lu2 sen1 bao3]
    Only return a Chinese for which this word is an abbreviation.
    """
    reference = regex.search(HAN_CHAR_REGEX, definition)
    if reference:
        reference = reference.group(0)
        reference = reference.split('|')
        return reference
    return


def handle_file(filename, output_file):
    out = MsgpackStreamWriter(output_file)

    for line in gzip.open(filename, 'rt'):

        # skip the intro information
        if line.startswith('#'):
            continue

        # parse the data to extract the traditional form, simplified form and the English definition
        traditional, simplified, definitions = re.match(LINE_REGEX, line).groups()

        # Make an edge between the traditional and simplified version
        edge = make_edge(rel='/r/Synonym',
                         start=standardized_concept_uri('zh-Hant', traditional),
                         end=standardized_concept_uri('zh-Hans', simplified),
                         dataset=DATASET,
                         license=LICENSE,
                         sources=SOURCE)
        out.write(edge)

        definitions = re.split(r'\/|;', definitions)
        for definition in definitions:

            # Skip pronunciation information
            if 'Taiwan pr.' in definition or 'also pr.' in definition:
                continue

            # Check if it's the definition matches a person syntax, i.e. includes a date range
            person_match = re.match(DATE_RANGE_REGEX, definition)
            if person_match:
                persons = extract_person(person_match)
                for person in persons:
                    edge = make_edge(rel='/r/Synonym',
                                     start=standardized_concept_uri('zh-Hant', traditional),
                                     end=standardized_concept_uri('en', person),
                                     dataset=DATASET,
                                     license=LICENSE,
                                     sources=SOURCE)
                    out.write(edge)

                    edge = make_edge(rel='/r/Synonym',
                                     start=standardized_concept_uri('zh-Hans', simplified),
                                     end=standardized_concept_uri('en', person),
                                     dataset=DATASET,
                                     license=LICENSE,
                                     sources=SOURCE)
                    out.write(edge)
                continue

            # Remove clarifying information in parenthesis
            definition = PAREN_REGEX.sub('', definition)

            # Check if a word is a measure word
            if definition.startswith('CL:'):
                related_words = extract_measure_words(definition)
                for word in related_words:
                    edge = make_edge(rel='/r/RelatedTo',
                                     start=standardized_concept_uri('zh-Hant', traditional),
                                     end=standardized_concept_uri('zh', word),
                                     dataset=DATASET,
                                     license=LICENSE,
                                     sources=SOURCE)
                    out.write(edge)

                    edge = make_edge(rel='/r/RelatedTo',
                                     start=standardized_concept_uri('zh-Hans', simplified),
                                     end=standardized_concept_uri('zh', word),
                                     dataset=DATASET,
                                     license=LICENSE,
                                     sources=SOURCE)
                    out.write(edge)
                continue

            # Check if a word is a form/variant of a different word
            variant_match = re.match(VARIANT_REGEX, definition)
            if variant_match:
                variants = extract_variants(definition)
                for variant in variants:
                    edge = make_edge(rel='/r/RelatedTo',
                                     start=standardized_concept_uri('zh-Hant', traditional),
                                     end=standardized_concept_uri('zh', variant),
                                     dataset=DATASET,
                                     license=LICENSE,
                                     sources=SOURCE)
                    out.write(edge)

                    edge = make_edge(rel='/r/RelatedTo',
                                     start=standardized_concept_uri('zh-Hans', simplified),
                                     end=standardized_concept_uri('zh', variant),
                                     dataset=DATASET,
                                     license=LICENSE,
                                     sources=SOURCE)
                    out.write(edge)
                continue

            # Handle abbreviations
            if re.match(ABBR_REGEX, definition):
                abbreviations = extract_abbreviations(definition)
                if abbreviations:
                    for abbr in abbreviations:
                        edge = make_edge(rel='/r/RelatedTo',
                                         start=standardized_concept_uri('zh-Hant', traditional),
                                         end=standardized_concept_uri('zh', abbr),
                                         dataset=DATASET,
                                         license=LICENSE,
                                         sources=SOURCE)
                        out.write(edge)

                        edge = make_edge(rel='/r/RelatedTo',
                                         start=standardized_concept_uri('zh-Hans', simplified),
                                         end=standardized_concept_uri('zh', abbr),
                                         dataset=DATASET,
                                         license=LICENSE,
                                         sources=SOURCE)
                        out.write(edge)
                continue

            # Remove 'lit.', 'fig.'
            definition = LIT_FIG_REGEX.sub('', definition)

            # Expand sth and sb
            definition = definition.replace('sth', 'something')
            definition = definition.replace('sb', 'someone')
            definition = remove_reference_syntax(definition)
            definition = remove_additional_info(definition)

            # Skip long definitions
            if len(definition.split()) < 6:
                edge = make_edge(rel='/r/Synonym',
                                 start=standardized_concept_uri('zh-Hant', traditional),
                                 end=standardized_concept_uri('en', definition),
                                 dataset=DATASET,
                                 license=LICENSE,
                                 sources=SOURCE)
                out.write(edge)

                edge = make_edge(rel='/r/RelatedTo',
                                 start=standardized_concept_uri('zh-Hans', simplified),
                                 end=standardized_concept_uri('en', definition),
                                 dataset=DATASET,
                                 license=LICENSE,
                                 sources=SOURCE)
                out.write(edge)
