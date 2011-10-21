"""
Utility functions for web interface.
"""

__author__ = 'Justin Venezuela (jven@mit.edu)'

def data_url(uri):
    return '/web/' + uri.strip('/')

def uri2name(arg):
    if arg.startswith('/concept'):
        if len(arg.split('/')) <= 3:
            return arg.split('/')[-1]
        result = arg.split('/')[3].replace('_', ' ')
    else:
        result = arg.split('/')[-1].replace('_', ' ')
    if result.startswith('be ') or result.startswith('to '):
        result = result[3:]
    return result
