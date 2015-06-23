from __future__ import unicode_literals
"""
Utility functions for web interface.

Gradually adapted from code by Justin Venezuela <jven@mit.edu>.
"""

import langcodes


# This list is for interface purposes only. We'll choose to show languages
# that have at least 10,000 edges in them.
SUPPORTED_LANGUAGE_CODES = [
    'af', 'ar', 'bg', 'ca', 'cs', 'cy', 'da', 'de', 'el', 'en', 'eo', 'es',
    'et', 'fa', 'fi', 'fo', 'fr', 'ga', 'gl', 'gv', 'he', 'hi', 'hu', 'hy',
    'io', 'is', 'it', 'ja', 'ka', 'ko', 'la', 'lt', 'lv', 'ms', 'nl', 'no',
    'pl', 'pt', 'ro', 'ru', 'sa', 'sh', 'sq', 'sv', 'syc', 'te', 'tr', 'ur',
    'vi', 'vo', 'zh'
]

def data_url(uri):
    return '/web/' + uri.strip('/')


def uri2name(arg):
    if arg.startswith('/c/'):
        if len(arg.split('/')) <= 3:
            return arg.split('/')[-1]
        result = arg.split('/')[3].replace('_', ' ')
    else:
        result = arg.split('/')[-1].replace('_', ' ')
    if result.startswith('be ') or result.startswith('to '):
        result = result[3:]
    return result


def get_sorted_languages():
    return [
        (lang, langcodes.get(lang).autonym())
        for lang in SUPPORTED_LANGUAGE_CODES
    ]
