# -*- coding: utf-8 -*-
"""
Concept Net 5
api.py file from conceptnet5 module
written by Rob Speer, Julian Chaidez
Common Sense Computing Group, Medialab
Massachusetts Institute of Technology
Fall 2011
"""

import flask
import urllib, urllib2
import re
import sys
import json
import os
import numpy as np
from assoc_space import AssocSpace
from werkzeug.contrib.cache import SimpleCache
app = flask.Flask(__name__)

commonsense_assoc = None
ASSOC_DIR = os.environ.get('CONCEPTNET_ASSOC_DATA') or '../data/assoc/space'
def load_assoc():
    """
    Load the association matrix. Requires the open source Python package
    'assoc_space'.
    """
    global commonsense_assoc
    if commonsense_assoc: return commonsense_assoc
    dirname = ASSOC_DIR
    commonsense_assoc = AssocSpace.load_dir(ASSOC_DIR)
    return commonsense_assoc

if len(sys.argv) == 1:
    root_url = 'http://conceptnet5.media.mit.edu/data/5.1'
else:
    root_url = sys.argv[1]

cache_dict = {
    'limit_timeout': 60,
    'limit_amount': 10000
}

request_cache = SimpleCache(default_timeout = cache_dict['limit_timeout'])

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
    if query_args.get('filter') == 'core-assertions':
        filter_params.append('dataset:/d/conceptnet/5/combined-core*')
        sharded = False
    elif query_args.get('filter') == 'core':
        sharded = False
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
        params['shards'] = 'localhost:8983/solr,claret.csc.media.mit.edu:8983/solr'
    if params['q'] == '':
        return see_documentation()
    return get_query_result(params)

SOLR_BASE = 'http://salmon.csc.media.mit.edu:8983/solr/select?'

def get_link(params):
    return SOLR_BASE + urllib.urlencode(params)

def get_query_result(params):
    link = get_link(params)
    print "Loading %s" % link
    fp = urllib2.urlopen(link)
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
    return flask.jsonify({'error':'invalid request'})

@app.route('/assoc/list/<lang>/<termlist>')
def list_assoc(lang, termlist):
    load_assoc()
    if commonsense_assoc is None:
        flask.abort(404)
    if isinstance(termlist, basestring):
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
    if '--unsafe' in sys.argv:
        app.debug = True
        app.run(debug=True, host='0.0.0.0', port=8084)
    else:
        app.run(debug=True, port=8084)
