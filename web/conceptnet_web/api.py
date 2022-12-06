"""
This file sets up Flask to serve the ConceptNet 5 API in JSON-LD format.
"""
import os

import flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from conceptnet5 import api as responses
from conceptnet5.api import VALID_KEYS, error
from conceptnet5.nodes import standardized_concept_uri
from conceptnet_web.error_logging import try_configuring_sentry
from conceptnet_web.filters import FILTERS
from conceptnet_web.json_rendering import jsonify

# Configuration

app = flask.Flask('conceptnet_web')
bp = flask.Blueprint('ignore', 'conceptnet_web' , template_folder='ignore')

def app_path(path):
    """
    Get a path next to the Flask app directory, where static files and
    templates may be.
    """
    return os.path.join(os.path.dirname(app.root_path), path)


app.config['RATELIMIT_ENABLED'] = os.environ.get('CONCEPTNET_RATE_LIMITING') == '1'

app.config.update({
    'JSON_AS_ASCII': False
})


for filter_name, filter_func in FILTERS.items():
    app.jinja_env.filters[filter_name] = filter_func
app.jinja_env.add_extension('jinja2_highlight.HighlightExtension')
limiter = Limiter(app, key_func=get_remote_address,
                  default_limits=["600 per minute", "6000 per hour"])
CORS(app)
try_configuring_sentry(app)
application = app  # for uWSGI


def get_int(args, key, default, minimum, maximum):
    strvalue = args.get(key, default)
    try:
        value = int(strvalue)
    except ValueError:
        value = default
    return max(minimum, min(maximum, value))


# Lookup: match any path starting with /a/, /c/, /d/, /r/, or /s/
@bp.route('/<any(a, c, d, r, s):top>/<path:query>')
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


@bp.route('/search')
@bp.route('/query')
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

@bp.route('/simplified-search')
@bp.route('/simplified-query')
def simplified_query():
    req_args = flask.request.args
    criteria = {}
    offset = get_int(req_args, 'offset', 0, 0, 100000)
    limit = get_int(req_args, 'limit', 50, 0, 1000)
    for key in flask.request.args:
        if key in VALID_KEYS:
            criteria[key] = flask.request.args[key]
    results = responses.simplified_query_paginated(criteria, offset=offset, limit=limit)
    return jsonify(results)

@bp.route('/search/count')
@bp.route('/query/count')
def query_count():
    """
    Count the number of edges matching a query.
    This supports Linked Data Fragments interfaces such as the 
    Triple Pattern Fragment
    """
    criteria = {}
    for key in flask.request.args:
        if key in VALID_KEYS:
            criteria[key] = flask.request.args[key]
    results = responses.query_count(criteria)
    return jsonify(results)

@bp.route('/simplified-search/count')
@bp.route('/simplified-query/count')
def simplified_query_count():
    """
    Count the number of edges matching a query.
    This supports Linked Data Fragments interfaces such as the 
    Triple Pattern Fragment
    """
    criteria = {}
    for key in flask.request.args:
        if key in VALID_KEYS:
            criteria[key] = flask.request.args[key]
    results = responses.simplified_query_count(criteria)
    return jsonify(results)



@bp.route('/uri')
@bp.route('/normalize')
@bp.route('/standardize')
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


@bp.route('/')
def see_documentation():
    """
    This function redirects to the api documentation
    """
    return jsonify({
        '@context': responses.CONTEXT,
        'rdfs:comment': 'See http://www.conceptnet.io for more information about ConceptNet, and http://api.conceptnet.io/docs for the API documentation.'
    })


@bp.route('/related/<path:uri>')
@limiter.limit("60 per minute")
def query_top_related(uri):
    req_args = flask.request.args
    uri = '/' + uri.rstrip('/ ')
    limit = get_int(req_args, 'limit', 50, 0, 100)
    filter = req_args.get('filter')
    results = responses.query_related(uri, filter=filter, limit=limit)
    return jsonify(results)


@bp.route('/relatedness')
@limiter.limit("60 per minute")
def query_relatedness():
    req_args = flask.request.args
    node1 = req_args.get('node1')
    node2 = req_args.get('node2')
    result = responses.query_relatedness(node1, node2)
    return jsonify(result)


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


# Visiting this URL intentionally causes an error, so we can see if Sentry
# is working. It has a silly name instead of just 'error' to decrease the
# probability of it being accidentally crawled.
@bp.route('/i-am-error')
def fake_error():
    raise Exception("Fake error for testing")


def render_error(status, details):
    return jsonify(error({}, status=status, details=details), status=status)

app.register_blueprint(bp, url_prefix=os.environ.get('APPLICATION_ROOT', ''))

if __name__ == '__main__':
    app.run(os.environ.get('HOSTNAME', '0.0.0.0'), debug=False, port=int(os.environ.get('PORT', '8084')))
