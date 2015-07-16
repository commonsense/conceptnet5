# coding: utf-8
from __future__ import unicode_literals
"""
Web interface for ConceptNet5.

Minimally updated in March 2014 to maintain compatibility. Slightly less
minimally updated in October 2014 to run in the same process as the JSON API.

It would be great to overhaul this, possibly replacing it with a static page
that just calls the JSON API.
"""

__author__ = 'Justin Venezuela (jven@mit.edu)'

# Python 2/3 compatibility
import sys
if sys.version_info.major < 3:
    from urllib import urlencode, quote
else:
    from urllib.parse import urlencode, quote

import os
import json
import re
import requests
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from conceptnet5.nodes import standardized_concept_uri
from conceptnet5.api import app
from conceptnet5.query import lookup
from conceptnet5.web_interface.utils import uri2name, get_sorted_languages

LANGUAGES = get_sorted_languages()

WEB_ROOT = '/web'

@app.route('/')
def root():
    return app.send_static_file('index.html')

@app.route(WEB_ROOT + '/')
def search_home():
    return render_template('home.html', languages=LANGUAGES)

@app.route(WEB_ROOT + '/concept/<path:uri>')
def concept_redirect(uri):
    return redirect(WEB_ROOT + '/c/'+uri)

@app.route(WEB_ROOT + '/relation/<path:uri>')
def rel_redirect(uri):
    return redirect(WEB_ROOT + '/r/'+uri)

@app.route(WEB_ROOT + '/search', methods=['POST'])
def web_search():
    keyword = request.form.get('keyword')
    lang = request.form.get('language')
    return redirect(WEB_ROOT + standardized_concept_uri(lang, keyword))

@app.route(WEB_ROOT + '/<path:uri>', methods=['GET'])
def edges_for_uri(uri):
    """
    This function replaces most functions in the old Web interface, as every
    query to the API now returns a list of edges.
    """
    uri = '/' + uri.rstrip('/')
    edges = list(lookup(uri, limit=100))
    seen_edges = {}
    out_edges = []
    caption = uri
    for edge in edges:
        switched = False
        if edge['uri'] not in seen_edges:
            url1 = WEB_ROOT+edge['start']
            url2 = WEB_ROOT+edge['end']
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
                url1 = WEB_ROOT+edge['start']
                url2 = WEB_ROOT+edge['end']
                linked1 = re.sub(r'\[\[([^\]]+)\]\]',
                    r'<a href="%s">\1</a>' % url1, text, count=1)
                linked2 = re.sub(r'\[\[([^\]]+)\]\]',
                    r'<a href="%s">\1</a>' % url2, linked1, count=1)
                oldedge['linked'] = linked2

    if not edges:
        return render_template('not_found.html', uri=uri, languages=LANGUAGES)
    else:
        return render_template('edges.html', uri=uri, caption=caption,
        edges=out_edges, root=WEB_ROOT, languages=LANGUAGES)

@app.errorhandler(404)
def handler404(error):
    return render_template('404.html', languages=LANGUAGES), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
