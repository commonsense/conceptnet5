#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
"""
In building ConceptNet, we often need to be able to map from language
names to language codes, or vice versa.

This is relevant, and complicated, when parsing Wiktionary. Entries identify
what language they're in using the name of the language. However, it's the
name of the language *in the language of the Wiktionary entry*.

So, for example, we will need to recognize that both 'English' and '古英語'
are English (en), and both 'Japanese' and '日本語' are Japanese.
"""

from whereami import get_project_filename
import codecs
import re

ISO_DATA_FILENAME = get_project_filename('data/codes/iso639.txt')

CODE_TO_ENGLISH_NAME = {}
ENGLISH_NAME_TO_CODE = {}

SUPPORTED_LANGUAGE_CODES = [
    'aa', 'ab', 'ae', 'af', 'ak', 'am', 'an', 'ar', 'as', 'ase', 'av', 'ay',
    'az', 'ba', 'be', 'bg', 'bh', 'bi', 'bm', 'bn', 'bo', 'br', 'bs', 'ca',
    'ce', 'ch', 'co', 'cr', 'cs', 'cu', 'cv', 'cy', 'da', 'de', 'dv', 'dz',
    'ee', 'el', 'en', 'eo', 'es', 'et', 'eu', 'fa', 'ff', 'fi', 'fj', 'fo',
    'fr', 'fy', 'ga', 'gd', 'gl', 'gn', 'gu', 'gv', 'ha', 'he', 'hi', 'ho',
    'hr', 'ht', 'hu', 'hy', 'hz', 'ia', 'id', 'ie', 'ig', 'ii', 'ik', 'io',
    'is', 'it', 'iu', 'ja', 'jv', 'ka', 'kg', 'ki', 'kj', 'kk', 'kl', 'km',
    'kn', 'ko', 'kr', 'ks', 'ku', 'kv', 'kw', 'ky', 'la', 'lb', 'lg', 'li',
    'ln', 'lo', 'lt', 'lu', 'lv', 'mg', 'mh', 'mi', 'mk', 'ml', 'mn', 'mr',
    'ms', 'mt', 'my', 'na', 'nb', 'nd', 'ne', 'ng', 'nl', 'nn', 'no', 'nr',
    'nv', 'ny', 'oc', 'oj', 'om', 'or', 'os', 'pa', 'pi', 'pl', 'ps', 'pt',
    'qu', 'rm', 'rn', 'ro', 'ru', 'rw', 'sa', 'sc', 'sco', 'sd', 'se', 'sg',
    'si', 'sk', 'sl', 'sm', 'sn', 'so', 'sq', 'sr', 'ss', 'st', 'su', 'sv',
    'sw', 'ta', 'te', 'tg', 'th', 'ti', 'tk', 'tl', 'tn', 'to', 'tr', 'ts',
    'tt', 'tw', 'ty', 'ug', 'uk', 'ur', 'uz', 've', 'vi', 'vo', 'wa', 'wo',
    'xh', 'yi', 'yo', 'za', 'zh', 'zu'
]

def _setup():
    first_line = True
    for line in codecs.open(ISO_DATA_FILENAME, encoding='utf-8'):
        if first_line:
            first_line = False
            continue
        alpha3, morecodes, alpha2, language_name = line.rstrip('\n').split('\t')
        codes = []
        if alpha2:
            # Not every language has an alpha2 code, but it should be first in
            # the list if it does.
            codes.append(alpha2)
        # Every language has an ISO 639-3 alpha3 code.
        codes.append(alpha3)

        # The second column contains ISO 639-2 alpha3 codes. Some
        # languages have two different codes, a "terminology" and a
        # "bibliographic" code, apparently by historical accident.
        # If this is the case, the entry will look like:
        #
        #    xxx / yyy*
        multi_code_match = re.match(r'(...) / (...)\*', morecodes)
        if multi_code_match:
            assert multi_code_match.group(1) == alpha3
            codes.append(multi_code_match.group(2))

        for code in codes:
            CODE_TO_ENGLISH_NAME[code] = language_name
        ENGLISH_NAME_TO_CODE[language_name] = codes[0]

_setup()
if __name__ == '__main__':
    for code in SUPPORTED_LANGUAGE_CODES:
        print("%-4s %s" % (code, CODE_TO_ENGLISH_NAME[code]))

