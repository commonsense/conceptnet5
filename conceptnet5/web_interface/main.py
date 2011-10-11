"""
Web interface for ConceptNet5.
"""

__author__ = 'Justin Venezuela (jven@mit.edu)'

import os
from flask import Flask
from flask import redirect
from flask import render_template
from flask import send_from_directory
from flask import url_for
from conceptnet5.graph import get_graph
import time

app = Flask(__name__)
conceptnet = get_graph()

def data_url(uri):
    # I appreciate that Justin had url_for here, but I can't get it to work
    # myself, so I'm cutting corners.
    return '/web/'+uri.strip('/')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'img'), 'favicon.ico',
        mimetype='image/vnd.microsoft.icon')

@app.route('/')
def home():
    return render_template('home.html')

def uri2name(arg):
    if arg.startswith('/concept'):
        return arg.split('/')[3].replace('_', ' ')
    else:
        return arg.split('/')[-1].replace('_', ' ')

@app.route('/web/<path:uri>')
def get_data(uri):
    uri = '/%s' % uri
    node = conceptnet.get_node(uri)
    # If node doesn't exist, say so.
    if node is None:
        return render_template('not_found.html', uri=uri)
    # Node exists, show stuff.
    incoming_edges = conceptnet.get_incoming_edges(node)

    assertions = []
    frames = []
    normalizations = []
    
    count = 0
    edge_generator = conceptnet.get_incoming_edges(uri, 'arg')
    for edge, assertion_uri in edge_generator:
        count += 1
        if count >= 50:
            break
        
        # Determine the relation and arguments from the URI.
        relargs = conceptnet.get_rel_and_args(assertion_uri)
        relation = relargs[0]
        args = relargs[1:]
        if len(args) != 2: continue
        # skip n-ary relations for now; I'm tired and we didn't implement them
        # successfully anyway. -- Rob
        
        linked_args = ['<a href="%s">%s</a>' % (data_url(arg), uri2name(arg))
                       for arg in args]
        readable_args = [uri2name(arg) for arg in args]
        if relation.startswith('/frame'):
            rendered_frame = uri2name(relation).replace('{%}', '').replace('{1}', linked_args[0])\
                                               .replace('{2}', linked_args[1])
            frames.append(rendered_frame)
        else:
            position = edge['position']
            if position == 1:
                otherNode = args[1]
                otherNodeName = readable_args[1]
            else:
                otherNode = args[0]
                otherNodeName = readable_args[0]
            assertions.append({
                'position': position,
                'relation': uri2name(relation),
                'relkey': "%s/%s" % (relation, position),
                'target_uri': otherNode,
                'target_url': data_url(otherNode),
                'target_text': otherNodeName,
                'score': edge['score']
            })

    normalized = None
    for edge, norm_uri in conceptnet.get_outgoing_edges(uri, 'normalized'):
        normalized = {
            'uri': norm_uri,
            'url': data_url(norm_uri),
            'name': uri2name(norm_uri)
        }
        break

    return render_template('data.html', node=node, assertions=assertions,
            frames=frames, normalized=normalized)

@app.errorhandler(404)
def handler404(error):
    return render_template('404.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
