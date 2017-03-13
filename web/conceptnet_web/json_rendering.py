from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments import highlight
from jinja2.ext import Markup
import flask
import re
import json


def request_wants_json():
    """
    Determine from the request headers whether this is a Web browser that wants
    pretty rendering, or an API user that wants actual JSON-LD.
    """
    if flask.request.args.get('format') == 'json':
        return True
    elif flask.request.args.get('format') == 'html':
        return False
    best = flask.request.accept_mimetypes \
        .best_match(['application/ld+json', 'application/json', 'text/html'])
    return (best is None) or ('json' in best)


def regex_replacement_stack(replacements):
    """
    Make a function that applies a sequence of regex replacements to text.
    """
    compiled_replacers = [(re.compile(match), replace) for (match, replace) in replacements]
    def _replace(text):
        for compiled_re, replacement in compiled_replacers:
            text = compiled_re.sub(replacement, text)
        return text
    return _replace


# These replacers convert absolute and relative URLs into links, and convert
# URIs in the cc: or lang: namespace to full URLs.
linker = regex_replacement_stack([
    (r'&quot;((https?://|/[acdrs]/)([^& ]|&amp;)*)&quot;', r'&quot;<a href="\1">\1</a>&quot;'),
    (r'&quot;cc:([^& ]+)&quot;', r'&quot;<a href="http://creativecommons.org/licenses/\1">cc:\1</a>&quot;'),
    (r'&quot;lang:([^& ]+)&quot;', r'&quot;<a href="http://www.lexvo.org/page/code/\1">cc:\1</a>&quot;')
])


def highlight_and_link_json(content):
    """
    Given JSON text, syntax-highlight it and convert URLs to links.
    """
    formatter = HtmlFormatter()
    lexer = get_lexer_by_name('json')
    html = highlight(content, lexer, formatter)
    urlized_html = linker(html)
    return Markup(urlized_html)


def jsonify(obj, status=200):
    """
    Our custom method for returning JSON, which either provides the raw JSON
    or fills in an HTML template with pretty, syntax-highlighted, linked JSON,
    depending on the requested content type.
    """
    if flask.request is None or request_wants_json():
        return flask.Response(
            json.dumps(obj, ensure_ascii=False, sort_keys=True),
            status=status,
            mimetype='application/json'
        )
    else:
        pretty_json = json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2)
        ugly_json = json.dumps(obj, ensure_ascii=False, sort_keys=True)
        return flask.render_template(
            'json.html',
            json=pretty_json,
            json_raw=ugly_json
        ), status
