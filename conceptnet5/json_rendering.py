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


def highlight_and_link_json(base_url):
    def _highlight_and_link_json(content):
        formatter = HtmlFormatter()
        lexer = get_lexer_by_name('json')
        html = highlight(content, lexer, formatter)
        urlized_html = re.sub(
            r'&quot;((https?://|/[acdrs]/)[^& ]*)&quot;',
            r'&quot;<a href="{}\1">\1</a>&quot;'.format(base_url),
            html
        )
        return Markup(urlized_html)
    return _highlight_and_link_json


def jsonify(obj):
    if flask.request is None or request_wants_json():
        return flask.Response(
            json.dumps(obj, ensure_ascii=False, sort_keys=True),
            mimetype='application/json'
        )
    else:
        pretty_json = json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2)
        ugly_json = json.dumps(obj, ensure_ascii=False, sort_keys=True)
        return flask.render_template(
            'json.html',
            json=pretty_json,
            json_raw=ugly_json
        )

