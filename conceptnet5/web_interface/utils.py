"""
Utility functions for web interface.
"""

__author__ = 'Justin Venezuela (jven@mit.edu)'

from conceptnet5.config import LANGUAGES

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
    keys = LANGUAGES.keys()
    non_ascii = []
    for key in keys:
        if ord(key[0]) > 127:
            non_ascii.append(key)
            keys.remove(key)
    sort = sorted(keys, key=str)
    for key in non_ascii:
        sort.append(key)
    
    #Return a dictionary that can be used in a template
    #containing the sorted list of keys and the actual
    #dictionary of languages
    return {"keys": sort, "languages": LANGUAGES}
