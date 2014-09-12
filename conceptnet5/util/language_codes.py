#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
"""
In building ConceptNet, we often need to be able to map from language
names to language codes, or vice versa.

So far, this is only supported for English and German names of languages,
although we will need translations of these names to say, parse entries from
the Japanese-language Wiktionary.

>>> CODE_TO_NAME['en']['fr']
'French'
>>> CODE_TO_NAME['en']['fra']
'French'
>>> NAME_TO_CODE['en']['French']
'fr'
>>> NAME_TO_CODE['en']['Mandarin']
'cmn'
>>> NAME_TO_CODE['de']['Dutch']
'ndl'
"""

from conceptnet5.util import get_support_data_filename
import codecs
import re

ISO_DATA_FILENAME = get_support_data_filename('iso639-enfrde.txt')

CODE_TO_NAME = {'en': {}, 'de': {}, 'fr': {}}
NAME_TO_CODE = {'en': {}, 'de': {}, 'fr': {}}

# The SUPPORTED_LANGUAGE_CODES are the ones that should appear in the
# browsable Web interface.
#
# This might be too many.
SUPPORTED_LANGUAGE_CODES = [
    'aa', 'ab', 'ae', 'af', 'ak', 'am', 'an', 'ar', 'as', 'av', 'ay',
    'az', 'ba', 'be', 'bg', 'bh', 'bi', 'bm', 'bn', 'bo', 'br', 'bs', 'ca',
    'ce', 'ch', 'co', 'cr', 'crh', 'cs', 'cu', 'cv', 'cy', 'da', 'de', 'dv',
    'dz', 'ee', 'el', 'en', 'eo', 'es', 'et', 'eu', 'fa', 'ff', 'fi', 'fj',
    'fo', 'fr', 'fy', 'ga', 'gd', 'gl', 'gn', 'gu', 'gv', 'ha', 'he', 'hi',
    'ho', 'hr', 'ht', 'hu', 'hy', 'hz', 'ia', 'id', 'ie', 'ig', 'ii', 'ik',
    'io', 'is', 'it', 'iu', 'ja', 'jv', 'ka', 'kg', 'ki', 'kj', 'kk', 'kl',
    'km', 'kn', 'ko', 'kr', 'ks', 'ku', 'kv', 'kw', 'ky', 'la', 'lb', 'lg',
    'li', 'ln', 'lo', 'lt', 'lu', 'lv', 'mg', 'mh', 'mi', 'mk', 'ml', 'mn',
    'mr', 'ms', 'mt', 'my', 'na', 'nb', 'nd', 'ne', 'ng', 'nl', 'nn',
    'no', 'nr', 'nv', 'ny', 'oc', 'oj', 'om', 'or', 'os', 'pa', 'pi', 'pl',
    'ps', 'pt', 'qu', 'rm', 'rn', 'ro', 'ru', 'rw', 'sa', 'sc', 'sco', 'sd',
    'se', 'sg', 'si', 'sk', 'sl', 'sm', 'sn', 'so', 'sq', 'sr', 'ss', 'st',
    'su', 'sv', 'sw', 'ta', 'te', 'tg', 'th', 'ti', 'tk', 'tl', 'tn', 'to',
    'tr', 'ts', 'tt', 'tw', 'ty', 'ug', 'uk', 'ur', 'uz', 've', 'vi', 'vo',
    'wa', 'wo', 'xh', 'yi', 'yo', 'za', 'zh', 'zu'
]


def _setup():
    """
    Read the tab-separated text file of language names, and create the
    forward and backward mappings between language codes and language names.
    """
    first_line = True
    for line in codecs.open(ISO_DATA_FILENAME, encoding='utf-8'):
        if first_line:
            first_line = False
            continue
        alpha3, alpha2, en_name, fr_name, de_name = line.rstrip('\n').split('\t')
        codes = []
        if alpha2:
            # Not every language has an alpha2 code, but it should be first in
            # the list if it does.
            codes.append(alpha2)
        # The first column contains ISO 639-2 alpha3 codes. Some
        # languages have two different codes, a "terminology" and a
        # "bibliographic" code, apparently by historical accident.
        # If this is the case, the entry will look like:
        #
        #    xxx (B),yyy (T)
        # We want the the "terminology" one.
        multi_code_match = re.match(r'(...) \(B\),(...) \(T\)', alpha3)
        if multi_code_match:
            codes.append(multi_code_match.group(1))
        else:
            codes.append(alpha3)

        for code in codes:
            CODE_TO_NAME['en'][code] = en_name
            CODE_TO_NAME['de'][code] = de_name
            CODE_TO_NAME['fr'][code] = fr_name
        NAME_TO_CODE['en'][en_name] = codes[0]
        NAME_TO_CODE['de'][de_name] = codes[0]
        NAME_TO_CODE['fr'][fr_name] = codes[0]

    # Add some exceptions not covered in the official standard
    NAME_TO_CODE['en']['Cantonese'] = 'yue'
    NAME_TO_CODE['de']['Lateinisch'] = 'la'
    NAME_TO_CODE['de']['Walisisch'] = 'cy'


_setup()
if __name__ == '__main__':
    not_found = []
    for code in SUPPORTED_LANGUAGE_CODES:
        try:
            print("%-4s %s" % (code, CODE_TO_NAME['en'][code]))
        except KeyError as e:
            not_found.append(str(e))

    for code in not_found:
        print("NOT FOUND: %s" % code)
