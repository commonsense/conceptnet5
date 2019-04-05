"""
This file sets up Flask to serve the ConceptNet 5 API in JSON-LD format.
"""
import os

import flask
from flask_limiter import Limiter

from conceptnet5 import api as responses
from conceptnet5.languages import COMMON_LANGUAGES, LANGUAGE_NAMES
from conceptnet5.nodes import standardized_concept_uri
from conceptnet5.uri import split_uri
from conceptnet_web.error_logging import try_configuring_sentry
from conceptnet_web.filters import FILTERS
from conceptnet_web.relations import REL_HEADINGS

# Configuration
app = flask.Flask('conceptnet_web')


def app_path(path):
    """
    Get a path next to the Flask app directory, where static files and
    templates may be.
    """
    return os.path.join(os.path.dirname(app.root_path), path)


app.config['RATELIMIT_ENABLED'] = os.environ.get('CONCEPTNET_RATE_LIMITING') == '1'

for filter_name, filter_func in FILTERS.items():
    app.jinja_env.filters[filter_name] = filter_func
limiter = Limiter(app, global_limits=["600 per minute", "6000 per hour"])
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
# @app.route('/<any(a, c, d, r, s):top>/<path:query>')
@app.route('/')
def front_page():
    languages = [(lang, LANGUAGE_NAMES[lang]) for lang in COMMON_LANGUAGES
                 if lang != 'mul']
    languages.sort(key=lambda item: item[1])
    return flask.render_template('index.html', languages=languages)


@app.route('/search')
def search_concept():
    req_args = flask.request.args
    lang = req_args.get('language', 'en')
    text = req_args.get('text', '').strip()
    uri = standardized_concept_uri(lang, text).rstrip('/')
    return flask.redirect(uri)


@app.route('/web/c/<path:uri>')
@app.route('/c/<path:uri>')
def browse_concept(uri):
    req_args = flask.request.args
    concept = '/c/%s' % uri
    pieces = split_uri(concept)
    if len(pieces) <= 2:
        return browse_node('c', pieces[1])
    limit = get_int(req_args, 'limit', 20, 0, 1000)

    # Offset is not used when grouping by features
    offset = get_int(req_args, 'offset', 0, 0, 10000)

    filters = {}
    for key in responses.VALID_KEYS:
        if key != 'node' and key in req_args:
            filters[key] = req_args[key]

    if filters:
        filters['node'] = concept
        limit = get_int(req_args, 'limit', 100, 0, 1000)
        return edge_list_query(filters, offset=offset, limit=limit)
    else:
        results = responses.lookup_grouped_by_feature(concept, filters, feature_limit=limit)
        sources = []

        if 'error' in results:
            return flask.render_template('error.html', error=results['error'])

        for feature in results['features']:
            rel = feature['feature']['rel']
            if rel in REL_HEADINGS['en']:
                label_choices = REL_HEADINGS['en'][rel]
            else:
                label_choices = ['%s {0}' % rel, '{0} %s' % rel]

            if feature['symmetric'] or 'end' in feature['feature']:
                feat_label = label_choices[0]
            else:
                feat_label = label_choices[1]
            feature['label'] = feat_label.format(results['label'])
            for edge in feature['edges']:
                sources.extend(edge['sources'])

        return flask.render_template(
            'node_by_feature.html', term=results, features=results['features'], sources=sources
        )


# Lookup: match any path starting with /a/, /c/, /d/, /r/, or /s/
@app.route('/web/<any(a, d, r, s):top>/<path:query>')
@app.route('/<any(a, d, r, s):top>/<path:query>')
def browse_node(top, query):
    # TODO: can we make this work with edge_list_query?
    req_args = flask.request.args
    path = '/%s/%s' % (top, query.strip('/'))
    offset = get_int(req_args, 'offset', 0, 0, 100000)
    limit = get_int(req_args, 'limit', 100, 0, 1000)
    results = responses.lookup_paginated(path, offset=offset, limit=limit)
    sources = []
    pageStart = offset + 1
    pageEnd = offset + max(1, min(limit, len(results['edges'])))

    for edge in results['edges']:
        sources.extend(edge['sources'])
    return flask.render_template(
        'edge_list.html', results=results, sources=sources,
        pageStart=pageStart, pageEnd=pageEnd
    )


@app.route('/query')
def query():
    req_args = flask.request.args
    criteria = {}
    offset = get_int(req_args, 'offset', 0, 0, 100000)
    limit = get_int(req_args, 'limit', 100, 0, 1000)
    for key in flask.request.args:
        if key in responses.VALID_KEYS:
            criteria[key] = flask.request.args[key]
    return edge_list_query(criteria, offset=offset, limit=limit)


def edge_list_query(criteria, offset=0, limit=50):
    results = responses.query_paginated(criteria, offset=offset, limit=limit)
    sources = []
    pageStart = offset + 1
    pageEnd = offset + max(1, min(limit, len(results['edges'])))
    if 'error' in results:
        return flask.render_template('error.html', error=results['error'])
    for edge in results['edges']:
        sources.extend(edge['sources'])
    return flask.render_template(
        'edge_list.html', results=results, sources=sources,
        pageStart=pageStart, pageEnd=pageEnd
    )


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
    return render_error(500, '%s: %s' % (e.__class__.__name__, e))


# Visiting this URL intentionally causes an error, so we can see if Sentry
# is working. It has a silly name instead of just 'error' to decrease the
# probability of it being accidentally crawled.
@app.route('/i-am-error')
def fake_error():
    raise Exception("Fake error for testing")


def render_error(status, details):
    return flask.render_template(
        'error.html', error={
            'status': status,
            'details': details
        }
    ), status


if __name__ == '__main__':
    app.debug = True
    app.run('127.0.0.1', debug=True, port=8084)
