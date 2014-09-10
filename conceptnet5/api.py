# -*- coding: utf-8 -*-
"""
This file serves the ConceptNet 5 JSON API, by connecting to a SQLite
index of all of ConceptNet 5.
"""
from __future__ import unicode_literals, print_function

import sys
import flask
from flask_cors import CORS
from werkzeug.contrib.cache import SimpleCache
from conceptnet5.query import AssertionFinder, VALID_KEYS
from conceptnet5.assoc_query import AssocSpaceWrapper, MissingAssocSpace
from conceptnet5.util import get_data_filename
app = flask.Flask(__name__)
CORS(app)

if not app.debug:
    import logging
    file_handler = logging.FileHandler('logs/flask_errors.log')
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)


### Configuration ###

FINDER = AssertionFinder()
ASSOC_WRAPPER = AssocSpaceWrapper(
    get_data_filename('assoc/assoc-space-5.3'), FINDER
)
commonsense_assoc = None

if len(sys.argv) == 1:
    root_url = 'http://conceptnet5.media.mit.edu/data/5.3'
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
    })


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

### Rate limiting ###

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


### API endpoints ###

@app.route('/<path:query>')
def query_node(query):
    # TODO: restore support for min_weight?
    req_args = flask.request.args
    path = '/' + query.strip('/')
    offset = int(req_args.get('offset', 0))
    offset = max(0, offset)
    limit = int(req_args.get('limit', 50))
    limit = max(0, min(limit, 1000))
    results = list(FINDER.lookup(path, offset=offset, limit=limit))
    return flask.jsonify(edges=results, numFound=len(results))


@app.route('/search')
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


@app.route('/')
def see_documentation():
    """
    This function redirects to the api documentation
    """
    return flask.redirect('https://github.com/commonsense/conceptnet5/wiki/API')


@app.route('/assoc/list/<lang>/<path:termlist>')
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


@app.route('/assoc/<path:uri>')
def concept_assoc(uri):
    uri = '/' + uri.rstrip('/')

    return assoc_for_termlist([(uri, 1.0)])


if __name__ == '__main__':
    app.debug = True
    app.run('127.0.0.1', debug=True, port=8084)
