"""
This file sets up Flask to serve the ConceptNet 5 API in JSON-LD format.
"""
from conceptnet_web.json_rendering import jsonify, highlight_and_link_json
from conceptnet_web import responses
from conceptnet_web.responses import VALID_KEYS, error
from conceptnet_web.filters import FILTERS
from conceptnet5.nodes import standardized_concept_uri
import flask
from flask_cors import CORS
from flask_limiter import Limiter
from raven.contrib.flask import Sentry
import logging
import os
# TODO: vector wrapper


# Configuration

WORKING_DIR = os.getcwd()
STATIC_PATH = os.environ.get('CONCEPTNET_WEB_STATIC', os.path.join(WORKING_DIR, 'static'))
TEMPLATE_PATH = os.environ.get('CONCEPTNET_WEB_TEMPLATES', os.path.join(WORKING_DIR, 'templates'))

app = flask.Flask(
    'conceptnet5',
    template_folder=TEMPLATE_PATH,
    static_folder=STATIC_PATH
)
app.config['JSON_AS_ASCII'] = False
app.config['RATELIMIT_ENABLED'] = os.environ.get('CONCEPTNET_RATE_LIMITING') == '1'


for filter_name, filter_func in FILTERS.items():
    app.jinja_env.filters[filter_name] = filter_func
app.jinja_env.add_extension('jinja2_highlight.HighlightExtension')
limiter = Limiter(app, global_limits=["600 per minute", "6000 per hour"])
CORS(app)
application = app  # for uWSGI


def get_int(args, key, default, minimum, maximum):
    strvalue = args.get(key, default)
    try:
        value = int(strvalue)
    except ValueError:
        value = default
    return max(minimum, min(maximum, value))


# Lookup: match any path starting with /a/, /c/, /d/, /r/, or /s/
@app.route('/<any(a, c, d, r, s):top>/<path:query>')
def query_node(top, query):
    req_args = flask.request.args
    path = '/%s/%s' % (top, query.strip('/'))
    offset = get_int(req_args, 'offset', 0, 0, 100000)
    limit = get_int(req_args, 'limit', 20, 0, 1000)
    grouped = req_args.get('grouped', 'false').lower() == 'true'
    if grouped:
        limit = min(limit, 100)
        results = responses.lookup_grouped_by_feature(path, feature_limit=limit)
    elif path.startswith('/a/'):
        results = responses.lookup_single_assertion(path)
    else:
        results = responses.lookup_paginated(path, offset=offset, limit=limit)
    return jsonify(results)


@app.route('/search')
@app.route('/query')
def query():
    req_args = flask.request.args
    criteria = {}
    offset = get_int(req_args, 'offset', 0, 0, 100000)
    limit = get_int(req_args, 'limit', 50, 0, 1000)
    for key in flask.request.args:
        if key in VALID_KEYS:
            criteria[key] = flask.request.args[key]
    results = responses.query_paginated(criteria, offset=offset, limit=limit)
    return jsonify(results)


@app.route('/uri')
@app.route('/normalize')
@app.route('/standardize')
def query_standardize_uri():
    """
    Look up the URI for a given piece of text. 'text' and 'language' should be
    given as parameters.
    """
    language = flask.request.args.get('language')
    text = flask.request.args.get('text') or flask.request.args.get('term')
    if not language:
        return render_error(400, "Please specify a 'language' parameter.")
    if not text:
        return render_error(400, "Please specify a 'text' parameter.")
    return jsonify({
        '@context': responses.CONTEXT,
        '@id': standardized_concept_uri(language, text)
    })


@app.route('/')
def see_documentation():
    """
    This function redirects to the api documentation
    """
    return jsonify({
        '@context': responses.CONTEXT,
        'rdfs:comment': 'See http://www.conceptnet.io for more information about ConceptNet, and http://api.conceptnet.io/docs for the API documentation.'
    })


@app.route('/related/<path:uri>')
@limiter.limit("60 per minute")
def query_top_related(uri):
    req_args = flask.request.args
    uri = '/' + uri.rstrip('/ ')
    limit = get_int(req_args, 'limit', 50, 0, 100)
    filter = req_args.get('filter')
    results = responses.query_related(uri, filter=filter, limit=limit)
    return jsonify(results)


@app.errorhandler(IOError)
@app.errorhandler(MemoryError)
def error_data_unavailable(e):
    return render_error(503, str(e))


@app.errorhandler(400)
def error_bad_request(e):
    return render_error(
        400, "Something's wrong with the URL %r." % flask.request.full_path
    )


@app.errorhandler(404)
def error_page_not_found(e):
    return render_error(
        404, "%r isn't a URL that we understand." % flask.request.path
    )


@app.errorhandler(500)
def internal_server_error(e):
    return render_error(
        500, "Internal server error"
    )


def render_error(status, details):
    return jsonify(error({}, status=status, details=details), status=status)


if __name__ == '__main__':
    app.debug = True
    app.run('127.0.0.1', debug=True, port=8084)


if not app.debug:
    # Error logging configuration -- requires SENTRY_DSN to be set to a valid
    # Sentry client key
    if os.environ.get('SENTRY_DSN'):
        sentry = Sentry(app, logging=True, level=logging.ERROR)
    else:
        sentry = None
