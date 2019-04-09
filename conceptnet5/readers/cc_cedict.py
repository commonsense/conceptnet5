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

ABBR_REGEX = re.compile(r'(\b|\s)abbr. (to|of|for)')  # abbreviations
BRACKETS_REGEX = re.compile(r'\[.+?\]')  # pronunciation
DATE_RANGE_REGEX = re.compile(r'(.+?)\s\(.+\d.+\),')  # date range
DEFINITIONS_REGEX = re.compile(r'/|;')  # separate definitions
HAN_CHAR_REGEX = regex.compile('([\p{IsIdeo}]+[\|·]?)+')  # Han characters
LINE_REGEX = re.compile(
    r'(.+)\s(.+)\[.+\]\s/(.+)/'
)  # separate traditional and simplified words
LIT_FIG_REGEX = re.compile(r'(\b|\s)(fig|lit).\s')  # literally/figuratively
PAREN_REGEX = re.compile(r'\(.+?\)')  # parenthesis
SB_REGEX = re.compile(r'\b(sb)\b')
STH_REGEX = re.compile(r'\b(sth)\b')
SEE_ALSO_REGEX = re.compile(r'see( also)?')  # see also
VARIANT_REGEX = re.compile(
    r'((old |Japanese )?variant of|archaic version of|also ' r'written|same as)\s'
)  # variant syntax


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
    Remove any information in a definition after the first comma. This part of the definition
    usually provides additional details. For example, in the definition such as 'Salt Lake City,
    capital of Utah', 'capital of Utah' is removed.
    """
    return definition.split(',')[0]


def extract_person(match):
    """
    Extract the name of a person mentioned in a definition. A person definition contains a
    date range (ex. when they were alive or active) and a biography sentence, for example:
    "Pierre-Auguste Renoir (1841-1919), French impressionist painter". Occasionally, two forms of a
    person's name are provided, as in "Maria Skłodowska-Curie or Marie Curie". In that case,
    we return both names and make an edge for each of them.
    """
    person = match.groups()[0]
    person = remove_additional_info(person)
    person = remove_reference_syntax(person)
    person = person.split(' or ')  # get both versions of a person's name
    return person


def extract_measure_words(definition):
    """
    Extract measure words (classifiers). Measure words are prefixed with "CL:" and separated by a
    comma. For example: "CL:枝[zhi1],根[gen1],個|个[ge4],把[ba3]"
    """
    words = definition[3:]  # skip 'CL:'
    words = words.split(',')  # separate each measure word
    words = [BRACKETS_REGEX.sub('', word) for word in words]
    measure_words = []
    for word in words:
        measure_words.extend(word.split('|'))  # separate variants of a measure word
    return measure_words


def extract_han_characters(definition):
    """
    Extract han characters. This is used when extracting variants, abbreviations and references
    to other characters.
    """
    chars = regex.search(HAN_CHAR_REGEX, definition)
    if chars:
        return chars.group(0).split('|')
    return []


def handle_file(filename, output_file):
    out = MsgpackStreamWriter(output_file)

    for line in gzip.open(filename, 'rt'):

        # skip the intro information
        if line.startswith('#'):
            continue

        # parse the data to extract the traditional form, simplified form and the English definition
        traditional, simplified, definitions = re.match(LINE_REGEX, line).groups()

        # Make an edge between the traditional and simplified version
        edge = make_edge(
            rel='/r/Synonym',
            start=standardized_concept_uri('zh-Hant', traditional),
            end=standardized_concept_uri('zh-Hans', simplified),
            dataset=DATASET,
            license=LICENSE,
            sources=SOURCE,
        )
        out.write(edge)

        for definition in re.split(DEFINITIONS_REGEX, definitions):

            # Skip pronunciation information
            if 'Taiwan pr.' in definition or 'also pr.' in definition:
                continue

            # Check if it's the definition matches a person syntax, i.e. includes a date range
            person_match = re.match(DATE_RANGE_REGEX, definition)
            if person_match:
                persons = extract_person(person_match)
                for person in persons:
                    edge = make_edge(
                        rel='/r/Synonym',
                        start=standardized_concept_uri('zh-Hant', traditional),
                        end=standardized_concept_uri('en', person),
                        dataset=DATASET,
                        license=LICENSE,
                        sources=SOURCE,
                    )
                    out.write(edge)

                    edge = make_edge(
                        rel='/r/Synonym',
                        start=standardized_concept_uri('zh-Hans', simplified),
                        end=standardized_concept_uri('en', person),
                        dataset=DATASET,
                        license=LICENSE,
                        sources=SOURCE,
                    )
                    out.write(edge)
                continue

            # Check if a word is a measure word
            if definition.startswith('CL:'):
                related_words = extract_measure_words(definition)
                for word in related_words:
                    edge = make_edge(
                        rel='/r/RelatedTo',
                        start=standardized_concept_uri('zh-Hant', traditional),
                        end=standardized_concept_uri('zh', word),
                        dataset=DATASET,
                        license=LICENSE,
                        sources=SOURCE,
                    )
                    out.write(edge)

                    edge = make_edge(
                        rel='/r/RelatedTo',
                        start=standardized_concept_uri('zh-Hans', simplified),
                        end=standardized_concept_uri('zh', word),
                        dataset=DATASET,
                        license=LICENSE,
                        sources=SOURCE,
                    )
                    out.write(edge)
                continue

            # Remove clarifying information in parenthesis
            definition = PAREN_REGEX.sub('', definition)

            # Handle variants/word forms and abbreviations
            if re.match(VARIANT_REGEX, definition) or re.match(ABBR_REGEX, definition):
                variants = extract_han_characters(definition)
                for variant in variants:
                    edge = make_edge(
                        rel='/r/Synonym',
                        start=standardized_concept_uri('zh-Hant', traditional),
                        end=standardized_concept_uri('zh', variant),
                        dataset=DATASET,
                        license=LICENSE,
                        sources=SOURCE,
                    )
                    out.write(edge)

                    edge = make_edge(
                        rel='/r/Synonym',
                        start=standardized_concept_uri('zh-Hans', simplified),
                        end=standardized_concept_uri('zh', variant),
                        dataset=DATASET,
                        license=LICENSE,
                        sources=SOURCE,
                    )
                    out.write(edge)
                continue

            if re.match(SEE_ALSO_REGEX, definition):
                references = extract_han_characters(definition)
                for reference in references:
                    edge = make_edge(
                        rel='/r/RelatedTo',
                        start=standardized_concept_uri('zh-Hant', traditional),
                        end=standardized_concept_uri('zh', reference),
                        dataset=DATASET,
                        license=LICENSE,
                        sources=SOURCE,
                    )
                    out.write(edge)

                    edge = make_edge(
                        rel='/r/RelatedTo',
                        start=standardized_concept_uri('zh-Hans', simplified),
                        end=standardized_concept_uri('zh', reference),
                        dataset=DATASET,
                        license=LICENSE,
                        sources=SOURCE,
                    )
                    out.write(edge)

            # Remove 'lit.', 'fig.'
            definition = LIT_FIG_REGEX.sub('', definition)

            # Expand sth and sb
            definition = SB_REGEX.sub('someone', definition)
            definition = STH_REGEX.sub('something', definition)

            # Additional cleanups
            definition = remove_reference_syntax(definition)
            definition = remove_additional_info(definition)

            # Skip long definitions and make an edge out of remaining information
            if len(definition.split()) < 6:
                edge = make_edge(
                    rel='/r/Synonym',
                    start=standardized_concept_uri('zh-Hant', traditional),
                    end=standardized_concept_uri('en', definition),
                    dataset=DATASET,
                    license=LICENSE,
                    sources=SOURCE,
                )
                out.write(edge)

                edge = make_edge(
                    rel='/r/Synonym',
                    start=standardized_concept_uri('zh-Hans', simplified),
                    end=standardized_concept_uri('en', definition),
                    dataset=DATASET,
                    license=LICENSE,
                    sources=SOURCE,
                )
                out.write(edge)
