# -*- coding: utf-8 -*-
"""
Concept Net 5
api.py file from conceptnet5 module
written by Rob Speer, Julian Chaidez
Common Sense Computing Group, Medialab
Massachusetts Institute of Technology
Fall 2011
"""

import string
import flask
import urllib, urllib2
import re
import sys
import json

from werkzeug.contrib.cache import SimpleCache
app = flask.Flask(__name__)

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

def request_limit(ip_address):
    """
    This function checks the query ip address and ensures that the requests from that
    address have not passed the query limit
    """
    if request_cache.get(ip_address) > cache_dict['limit_amount']:
        return True, flask.Response(
          response=flask.json.dumps({'unauthorized':'rate limit violated'}),
          status=401, mimetype='json')
    else:
        request_cache.inc(ip_address, 1)
        return False, None

@app.route('/<path:query>')
def query_node(query):
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
    return search({'nodes': path})

LUCENE_SPECIAL_RE = re.compile(r'([-+!(){}\[\]^"~*?:\\])')

def lucene_escape(text):
    result = LUCENE_SPECIAL_RE.sub(r'\\\1', text)
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
    params['q'] = ' AND '.join(query_params)
    params['fq'] = ' AND '.join(filter_params)
    params['start'] = query_args.get('offset', '0')
    params['rows'] = query_args.get('limit', '50')
    params['fl'] = '*,score'
    params['wt'] = 'json'
    params['indent'] = 'on'
    if sharded:
        params['shards'] = 'localhost:8983/solr,callisto.csc.media.mit.edu:8983/solr'
    return get_query_result(params)

SOLR_BASE = 'http://amalthea.csc.media.mit.edu:8983/solr/select?'

def get_link(params):
    return SOLR_BASE + urllib.urlencode(params)

def get_query_result(params):
    link = get_link(params)
    print "Loading %s" % link
    fp = urllib2.urlopen(link)
    obj = json.load(fp)
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

if __name__ == '__main__':
    if '--unsafe' in sys.argv:
        app.run(debug=True, host='0.0.0.0', port=5002)
    else:
        app.run(debug=True, port=5002)
