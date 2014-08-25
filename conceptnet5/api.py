# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
"""
This file serves the ConceptNet 5 JSON API, by connecting to a SQLite
index of all of ConceptNet 5.
"""

import sys
import os
import flask
from werkzeug.contrib.cache import SimpleCache
from conceptnet5.query import AssertionFinder, VALID_KEYS
from conceptnet5.util import get_data_filename
app = flask.Flask(__name__)

if not app.debug:
    import logging
    file_handler = logging.FileHandler('logs/flask_errors.log')
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

FINDER = AssertionFinder()
ASSOC_DIR = get_data_filename('assoc/space')
commonsense_assoc = None


def configure_api(db_path, assertion_dir, assoc_dir=None, nshards=8):
    """
    Override the usual AssertionFinder with a new one, possibly with different
    settings. Do the same for the assoc_dir if given.

    This is useful for testing.
    """
    global FINDER, ASSOC_DIR
    FINDER = AssertionFinder(db_path, assertion_dir, nshards)
    ASSOC_DIR = assoc_dir
    if assoc_dir is not None:
        load_assoc()


def load_assoc():
    """
    Load the association matrix. Requires the open source Python package
    'assoc_space'.
    """
    from assoc_space import AssocSpace
    global commonsense_assoc
    if commonsense_assoc:
        return commonsense_assoc
    commonsense_assoc = AssocSpace.load_dir(ASSOC_DIR)
    return commonsense_assoc

if len(sys.argv) == 1:
    root_url = 'http://conceptnet5.media.mit.edu/data/5.3'
else:
    root_url = sys.argv[1]

cache_dict = {
    'limit_timeout': 60,
    'limit_amount': 10000
}

request_cache = SimpleCache(default_timeout=cache_dict['limit_timeout'])


def request_limit(ip_address, amount=1):
    """
    This function checks the query ip address and ensures that the requests
    from that address have not passed the query limit.
    """
    if request_cache.get(ip_address) > cache_dict['limit_amount']:
        return True, flask.Response(
            response=flask.json.dumps({'error': 'rate limit exceeded'}),
            status=429, mimetype='json'
        )
    else:
        request_cache.inc(ip_address, amount)
        return False, None


@app.route('/<path:query>')
def query_node(query):
    # TODO: restore support for min_weight?
    req_args = flask.request.args
    path = '/' + query.strip('/')
    offset = int(req_args.get('offset', 0))
    limit = int(req_args.get('limit', 50))
    results = list(FINDER.lookup(path, offset=offset, limit=limit))
    return flask.jsonify(edges=results, numFound=len(results))


@app.route('/search')
def search():
    criteria = {}
    offset = int(flask.request.args.get('offset', 0))
    limit = int(flask.request.args.get('limit', 50))
    for key in flask.request.args:
        if key in VALID_KEYS:
            criteria[key] = flask.request.args[key]
    results = list(FINDER.query(criteria, limit=limit, offset=offset))
    return flask.jsonify(edges=results, numFound=len(results))


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
    if limit > 1000:
        limit = 20

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
