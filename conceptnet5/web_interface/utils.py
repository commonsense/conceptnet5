from __future__ import unicode_literals
"""
Utility functions for web interface.
"""

__author__ = 'Justin Venezuela (jven@mit.edu)'

from conceptnet5.util.language_codes import SUPPORTED_LANGUAGE_CODES, CODE_TO_ENGLISH_NAME


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
        (lang, CODE_TO_ENGLISH_NAME[lang])
        for lang in SUPPORTED_LANGUAGE_CODES
    ]
