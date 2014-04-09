"""
Web interface for ConceptNet5.

Minimally updated in March 2014 to maintain compatibility, but it needs to be
revised.
"""

__author__ = 'Justin Venezuela (jven@mit.edu)'

# Python 2/3 compatibility
import sys
if sys.version_info.major < 3:
    from urllib import urlencode, quote
    from urllib2 import urlopen
else:
    from urllib.parse import urlencode, quote
    from urllib.request import urlopen

import os
import json
import re
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from conceptnet5.nodes import normalized_concept_uri
from conceptnet5.web_interface.utils import uri2name, get_sorted_languages

LANGUAGES = get_sorted_languages()

########################
# Set this flag to True when developing, False otherwise! -JVen
#
DEVELOPMENT = False
#
########################

app = Flask(__name__)

if DEVELOPMENT:
  site = 'http://new-caledonia.media.mit.edu:8080'
  web_root = ''
else:
  site = 'http://conceptnet5.media.mit.edu'
  web_root = '/web'

json_root = 'http://conceptnet5.media.mit.edu/data/5.2/'

import logging
file_handler = logging.FileHandler('logs/web_errors.log')
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

def get_json_from_uri(uri, params):
    url = uri.lstrip(u'/')
    url_bytes = url.encode('utf-8')
    url_quoted = quote(url_bytes)
    params_quoted = urlencode(params)
    if params_quoted:
        params_quoted = '?'+params_quoted
    full_url = json_root + url_quoted + params_quoted
    return json.load(urlopen(full_url))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'img'), 'favicon.ico',
        mimetype='image/vnd.microsoft.icon')

@app.route('/')
def home():
    return render_template('home.html', languages=LANGUAGES)
    
@app.route('/concept/<path:uri>')
def concept_redirect(uri):
    return redirect(site + web_root + '/c/'+uri)

@app.route('/relation/<path:uri>')
def rel_redirect(uri):
    return redirect(site + web_root + '/r/'+uri)

@app.route('/search', methods=['POST'])
def search():
    keyword = request.form.get('keyword')
    lang = request.form.get('language')
    return redirect(site + web_root + normalized_concept_uri(lang, keyword))

@app.route('/<path:uri>', methods=['GET'])
def edges_for_uri(uri):
    """
    This function replaces most functions in the old Web interface, as every
    query to the API now returns a list of edges.
    """
    uri = u'/'+uri.rstrip(u'/')
    response = get_json_from_uri(uri, {'limit': 100})
    edges = response.get('edges', [])
    seen_edges = {}
    out_edges = []
    caption = uri
    for edge in edges:
        switched = False
        if edge['uri'] not in seen_edges:
            url1 = web_root+edge['start']
            url2 = web_root+edge['end']
            edge['startName'] = uri2name(edge['start'])
            edge['relName'] = uri2name(edge['rel'])
            edge['endName'] = uri2name(edge['end'])
            text = edge.get('surfaceText') or ''
            if caption == uri and edge['start'] == uri:
                caption = edge['startName']
            if caption == uri and edge['end'] == uri:
                caption = edge['endName']

            ## possible guess:
            #  "[[%s]] %s [[%s]]" %\
            #  (uri2name(edge['start']), uri2name(edge['rel']),
            #   uri2name(edge['end']))

            linked1 = re.sub(r'\[\[([^\]]+)\]\]',
                r'<a href="%s">\1</a>' % url1, text, count=1)
            linked2 = re.sub(r'\[\[([^\]]+)\]\]',
                r'<a href="%s">\1</a>' % url2, linked1, count=1)
            edge['linked'] = linked2
            out_edges.append(edge)
            seen_edges[edge['uri']] = edge
        else:
            oldedge = seen_edges[edge['uri']]
            oldedge['score'] += edge['score']
            if not oldedge.get('linked'):
                text = edge.get('surfaceText') or ''
                url1 = web_root+edge['start']
                url2 = web_root+edge['end']
                linked1 = re.sub(r'\[\[([^\]]+)\]\]',
                    r'<a href="%s">\1</a>' % url1, text, count=1)
                linked2 = re.sub(r'\[\[([^\]]+)\]\]',
                    r'<a href="%s">\1</a>' % url2, linked1, count=1)
                oldedge['linked'] = linked2

    if not edges:
        return render_template('not_found.html', uri=uri, languages=LANGUAGES)
    else:
        return render_template('edges.html', uri=uri, caption=caption,
        edges=out_edges, root=web_root, languages=LANGUAGES)

@app.errorhandler(404)
def handler404(error):
    return render_template('404.html', languages=LANGUAGES)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
