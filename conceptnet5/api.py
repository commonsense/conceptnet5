# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
"""
This file serves the ConceptNet 5 JSON API, by connecting to a Solr
index of all of ConceptNet 5.

It was written in Fall 2011 by Julian Chaidez and Rob Speer, and
updated in March 2014 to account for Python 3 and the code refactor.

It should probably be revised more, but there's a good chance that
we will be replacing the Solr index with something else.
"""

# Python 2/3 compatibility
import sys
if sys.version_info.major < 3:
    from urllib import urlencode
    from urllib2 import urlopen
else:
    from urllib.parse import urlencode
    from urllib.request import urlopen

import flask
import re
import json
import os
from werkzeug.contrib.cache import SimpleCache
app = flask.Flask(__name__)

if not app.debug:
    import logging
    file_handler = logging.FileHandler('logs/flask_errors.log')
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

ASSOC_DIR = os.environ.get('CONCEPTNET_ASSOC_DATA') or '../data/assoc/space'
commonsense_assoc = None
def load_assoc():
    """
    Load the association matrix. Requires the open source Python package
    'assoc_space'.
    """
    from assoc_space import AssocSpace
    global commonsense_assoc
    if commonsense_assoc: return commonsense_assoc
    commonsense_assoc = AssocSpace.load_dir(ASSOC_DIR)
    return commonsense_assoc

if len(sys.argv) == 1:
    root_url = 'http://conceptnet5.media.mit.edu/data/5.2'
else:
    root_url = sys.argv[1]

cache_dict = {
    'limit_timeout': 60,
    'limit_amount': 10000
}

request_cache = SimpleCache(default_timeout=cache_dict['limit_timeout'])

def add_slash(uri):
    """
    Ensures that a slash is present in all situations where slashes are
    absolutely necessary for an address.
    """
    if uri[0] == '/':
        return uri
    else:
        return '/' + uri

def request_limit(ip_address, amount=1):
    """
    This function checks the query ip address and ensures that the requests
    from that address have not passed the query limit.
    """
    if request_cache.get(ip_address) > cache_dict['limit_amount']:
        return True, flask.Response(
          response=flask.json.dumps({'error': 'rate limit exceeded'}),
          status=429, mimetype='json')
    else:
        request_cache.inc(ip_address, amount)
        return False, None

@app.route('/<path:query>')
def query_node(query):
    req_args = flask.request.args
    path = '/'+query.strip('/')
    key = None
    if path.startswith('/c/') or path.startswith('/r/'):
        key = 'nodes'
    elif path.startswith('/a/'):
        key = 'uri'
    elif path.startswith('/d/'):
        key = 'dataset'
    elif path.startswith('/l/'):
        key = 'license'
    elif path.startswith('/s/'):
        key = 'sources'
    if key is None:
        flask.abort(404)
    query_args = {key: path}

    # Take some parameters that will be passed on to /search
    query_args['offset'] = req_args.get('offset', '0')
    query_args['limit'] = req_args.get('limit', '50')
    query_args['filter'] = req_args.get('filter', '')
    return search(query_args)

# This is one reason I want to get away from Solr.
LUCENE_SPECIAL_RE = re.compile(r'([-+!(){}\[\]^"~*?:\\])')

def lucene_escape(text):
    text = LUCENE_SPECIAL_RE.sub(r'\\\1', text)
    if ' ' in text:
        return '"%s"' % text
    else:
        return text

PATH_FIELDS = ['id', 'uri', 'rel', 'start', 'end', 'dataset', 'license', 'nodes', 'context', 'sources']
TEXT_FIELDS = ['surfaceText', 'text', 'startLemmas', 'endLemmas', 'relLemmas']
STRING_FIELDS = ['features']

@app.route('/search')
def search(query_args=None):
    if query_args is None:
        query_args = flask.request.args
    query_params = []
    filter_params = []
    sharded = True
    if query_args.get('filter') in ('core', 'core-assertions'):
        # core-assertions is equivalent to core, now that assertions are the
        # only edge-like structures the API returns.
        filter_params.append('license:/l/CC/By')
    for key in PATH_FIELDS:
        if key in query_args:
            val = lucene_escape(query_args.get(key)).rstrip('/')
            query_params.append("%s:%s" % (key, val))
            filter_params.append("%s:%s*" % (key, val))
    for key in TEXT_FIELDS + STRING_FIELDS:
        if key in query_args:
            val = lucene_escape(query_args.get(key)).rstrip('/')
            query_params.append("%s:%s" % (key, val))
    if 'minWeight' in query_args:
        try:
            weight = float(query_args.get('minWeight'))
        except ValueError:
            flask.abort(400)
        filter_params.append("weight:[%s TO *]" % weight)

    params = {}
    params['q'] = u' AND '.join(query_params).encode('utf-8')
    params['fq'] = u' AND '.join(filter_params).encode('utf-8')
    params['start'] = query_args.get('offset', '0')
    params['rows'] = query_args.get('limit', '50')
    params['fl'] = '*,score'
    params['wt'] = 'json'
    params['indent'] = 'on'
    if sharded:
        params['shards'] = 'burgundy.media.mit.edu:8983/solr,claret.media.mit.edu:8983/solr'
    if params['q'] == '':
        return see_documentation()
    return get_query_result(params)

SOLR_BASE = 'http://salmon.media.mit.edu:8983/solr/select?'

def get_link(params):
    return SOLR_BASE + urlencode(params)

def get_query_result(params):
    link = get_link(params)
    fp = urlopen(link)
    obj = json.load(fp)
    #obj['response']['params'] = params
    obj['response']['edges'] = obj['response']['docs']
    del obj['response']['docs']
    del obj['response']['start']
    return flask.jsonify(obj['response'])

@app.route('/')
def see_documentation():
    """
    This function redirects to the api documentation
    """
    return flask.redirect('https://github.com/commonsense/conceptnet5/wiki/API')

@app.errorhandler(404)
def not_found(error):
    return flask.jsonify({
       'error': 'invalid request',
       'details': str(error)
    })

@app.route('/assoc/list/<lang>/<termlist>')
def list_assoc(lang, termlist):
    load_assoc()
    if commonsense_assoc is None:
        flask.abort(404)
    if isinstance(termlist, bytes):
        termlist = termlist.decode('utf-8')

    terms = []
    try:
        term_pieces = termlist.split(',')
        for piece in term_pieces:
            piece = piece.strip()
            if '@' in piece:
                term, weight = piece.split('@')
                weight = float(weight)
            else:
                term = piece
                weight = 1.
            terms.append(('/c/%s/%s' % (lang, term), weight))
    except ValueError:
        flask.abort(400)
    return assoc_for_termlist(terms, commonsense_assoc)

def assoc_for_termlist(terms, assoc):
    limit = flask.request.args.get('limit', '20')
    limit = int(limit)
    if limit > 1000: limit=20

    filter = flask.request.args.get('filter')
    def passes_filter(uri):
        return filter is None or uri.startswith(filter)

    vec = assoc.vector_from_terms(terms)
    similar = assoc.terms_similar_to_vector(vec)
    similar = [item for item in similar if item[1] > 0 and
               passes_filter(item[0])][:limit]

    return flask.jsonify({'terms': terms, 'similar': similar})

@app.route('/assoc/<path:uri>')
def concept_assoc(uri):
    load_assoc()
    uri = '/' + uri.rstrip('/')
    if commonsense_assoc is None:
        flask.abort(404)

    return assoc_for_termlist([(uri, 1.0)], commonsense_assoc)

if __name__ == '__main__':
    app.debug = True
    app.run('127.0.0.1', debug=True, port=8084)
