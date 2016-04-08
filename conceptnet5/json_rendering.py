from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments import highlight
from jinja2.ext import Markup
import flask
import re
import json


def request_wants_json():
    best = flask.request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json'


def urlize_quoted_links(content):
    """
    Convert URLs (including relative URLs) to links in prettified JSON
    responses. Adapted from Tom Christie's flask_api.
    """


def highlight_json(content):
    formatter = HtmlFormatter()
    lexer = get_lexer_by_name('json')
    html = highlight(content, lexer, formatter)
    urlized_html = re.sub(r'&quot;((https?://|/[acdlrs]/)[^& ]*)&quot;', r'&quot;<a href="\1">\1</a>&quot;', html)
    return Markup(urlized_html)


def jsonify(obj):
    if flask.request is None or request_wants_json():
        return flask.Response(
            json.dumps(obj, ensure_ascii=False),
            mimetype='application/json'
        )
    else:
        pretty_json = json.dumps(obj, ensure_ascii=False, indent=2)
        return flask.render_template(
            'json.html',
            json=pretty_json,
        )

