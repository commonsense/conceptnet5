# -*- coding: utf-8 -*-
"""
This file serves the ConceptNet 5 JSON API, by connecting to a SQLite
index of all of ConceptNet 5.
"""
from __future__ import unicode_literals, print_function

import sys
import os
import flask
from flask_cors import CORS
from flask_limiter import Limiter
from conceptnet5 import __version__ as VERSION
from conceptnet5.nodes import standardized_concept_uri
from conceptnet5.query import AssertionFinder, VALID_KEYS
from conceptnet5.assoc_query import AssocSpaceWrapper, MissingAssocSpace, get_assoc_data
from conceptnet5.util import get_data_filename, get_support_data_filename



### Configuration ###

API_URL = '/data/%s' % VERSION
WORKING_DIR = os.getcwd()
STATIC_PATH = os.environ.get('CONCEPTNET_WEB_STATIC', os.path.join(WORKING_DIR, 'static'))
TEMPLATE_PATH = os.environ.get('CONCEPTNET_WEB_TEMPLATES', os.path.join(WORKING_DIR, 'templates'))

FINDER, ASSOC_WRAPPER = get_assoc_data('assoc-space-%s' % VERSION)

app = flask.Flask(
    'conceptnet5',
    template_folder=TEMPLATE_PATH,
    static_folder=STATIC_PATH
)
app.config['JSON_AS_ASCII'] = False
limiter = Limiter(app, global_limits=["600 per minute", "6000 per hour"])
CORS(app)

if len(sys.argv) == 1:
    root_url = 'http://conceptnet5.media.mit.edu/data/%s' % VERSION
else:
    root_url = sys.argv[1]


def configure_api(db_path, assertion_dir, assoc_dir=None, nshards=8):
    """
    Override the usual AssertionFinder with a new one, possibly with different
    settings. Do the same for the assoc_dir if given.

    This is useful for testing.
    """
    global FINDER, ASSOC_WRAPPER
    FINDER = AssertionFinder(db_path, assertion_dir, nshards)
    ASSOC_WRAPPER = AssocSpaceWrapper(assoc_dir, FINDER)


### Error handling ###

@app.errorhandler(404)
def not_found(error):
    return flask.jsonify({
        'error': 'invalid request',
        'details': str(error)
    }), 404


@app.errorhandler(MissingAssocSpace)
def missing_assoc_space(error):
    return flask.jsonify({
        'error': 'Feature unavailable',
        'details': error.args[0]
    }), 503


@app.errorhandler(ValueError)
def term_list_error(error):
    return flask.jsonify({
        'error': 'Invalid request',
        'details': error.args[0]
    }), 400


### API endpoints ###

@app.route(API_URL + '/<path:query>')
def query_node(query):
    req_args = flask.request.args
    path = '/' + query.strip('/')
    offset = int(req_args.get('offset', 0))
    offset = max(0, offset)
    limit = int(req_args.get('limit', 50))
    limit = max(0, min(limit, 1000))
    grouped = req_args.get('grouped', 'false').lower() == 'true'
    if grouped:
        limit = min(limit, 100)
        results = FINDER.lookup_grouped_by_feature(path, offset=offset, group_limit=limit)
        return flask.jsonify(groups=results)
    else:
        results = list(FINDER.lookup(path, offset=offset, limit=limit))
        return flask.jsonify(edges=results, numFound=len(results))


@app.route(API_URL + '/search')
def search():
    criteria = {}
    offset = int(flask.request.args.get('offset', 0))
    offset = max(0, offset)
    limit = int(flask.request.args.get('limit', 50))
    limit = max(0, min(limit, 1000))
    for key in flask.request.args:
        if key in VALID_KEYS:
            criteria[key] = flask.request.args[key]
    results = list(FINDER.query(criteria, limit=limit, offset=offset))
    return flask.jsonify(edges=results, numFound=len(results))


@app.route(API_URL + '/uri')
@app.route(API_URL + '/normalize')
@app.route(API_URL + '/standardize')
def standardize_uri():
    """
    Look up the URI for a given piece of text. 'text' and 'language' should be
    given as parameters.
    """
    language = flask.request.args.get('language')
    text = flask.request.args.get('text') or flask.request.args.get('term')
    if text is None or language is None:
        return flask.jsonify({
            'error': 'Invalid request',
            'details': "You should include the 'text' and 'language' parameters"
        }), 400
    text = text.replace('_', ' ')
    uri = standardized_concept_uri(language, text)
    return flask.jsonify(uri=uri)


@app.route(API_URL + '/')
def see_documentation():
    """
    This function redirects to the api documentation
    """
    return flask.redirect('https://github.com/commonsense/conceptnet5/wiki/API')


@app.route(API_URL + '/assoc/list/<lang>/<path:termlist>')
@limiter.limit("60 per minute")
def list_assoc(lang, termlist):
    if isinstance(termlist, bytes):
        termlist = termlist.decode('utf-8')

    terms = []
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

    return assoc_for_termlist(terms)


def assoc_for_termlist(terms):
    limit = flask.request.args.get('limit', '20')
    limit = max(0, min(int(limit), 1000))
    filter = flask.request.args.get('filter')

    similar = ASSOC_WRAPPER.associations(terms, filter=filter, limit=limit)
    return flask.jsonify({'terms': terms, 'similar': similar})


@app.route(API_URL + '/assoc/<path:uri>')
@limiter.limit("60 per minute")
def concept_assoc(uri):
    uri = '/' + uri.rstrip('/')
    return assoc_for_termlist([(uri, 1.0)])


if __name__ == '__main__':
    app.debug = True
    app.run('127.0.0.1', debug=True, port=8084)
