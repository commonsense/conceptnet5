"""
Web interface for ConceptNet5.
"""

__author__ = 'Justin Venezuela (jven@mit.edu)'

import itertools
import os
import time
from flask import Flask
from flask import redirect
from flask import render_template
from flask import send_from_directory
from flask import url_for
from utils import data_url
from utils import uri2name
from conceptnet5.graph import get_graph

app = Flask(__name__)
conceptnet = get_graph()

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'img'), 'favicon.ico',
        mimetype='image/vnd.microsoft.icon')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/random_assertion')
def random_assertion():
    # TODO(jven): For now, just use an arbitrary assertion.
    #for assertion in conceptnet.get_random_assertions():
    #    # Just use the first one.
    #    return assertion
    assertion_rel_args = conceptnet.get_rel_and_args('/assertion/[/concept/en/'
        'be_style_of/,/concept/en/ragtime/,/concept/en/music/]')
    relation_uri = assertion_rel_args[0]
    relation_url = data_url(relation_uri)
    relation_name = uri2name(relation_uri)
    args_uri = assertion_rel_args[1:]
    if len(args_uri) > 2:
        return 'n-ary assertions not supported at this time.'
    args_url = [data_url(arg_uri) for arg_uri in args_uri]
    args_name = [uri2name(arg_uri) for arg_uri in args_uri]
    assertion = {
        'source_name':args_name[0],
        'source_uri':args_uri[0],
        'source_url':args_url[0],
        'relation_name':relation_name,
        'relation_uri':relation_uri,
        'relation_url':relation_url,
        'target_name':args_name[1],
        'target_uri':args_uri[1],
        'target_url':args_url[1]
    }
    return render_template('vote.html', assertion=assertion)

@app.route('/<path:uri>')
def get_data(uri):
    uri = '/%s' % uri
    node = conceptnet.get_node(uri)
    # If node doesn't exist, say so.
    if node is None:
        return render_template('not_found.html', uri=uri)
    # Node exists, show stuff.
    incoming_edges = conceptnet.get_incoming_edges(node, result_limit=100)

    assertions = []
    frames = []
    normalizations = []

    count = 0
    edge_generator = itertools.chain(
        conceptnet.get_incoming_edges(uri, 'relation', result_limit=100),
        conceptnet.get_incoming_edges(uri, 'arg', result_limit=100)
    )

    timer = None
    for edge, assertion_uri in edge_generator:
        count += 1

        # Get 10 concepts, then however many concepts you can
        # retrieve in 1/5 more second, or at most 200.
        if count >= 10 and timer is None:
            timer = time.time()
        if (timer is not None and time.time() - timer > 0.2):
            break

        # Determine the relation and arguments from the URI.
        relargs = conceptnet.get_rel_and_args(assertion_uri)
        relation = relargs[0]
        args = relargs[1:]

        # skip n-ary relations for now; I'm tired and we didn't implement them
        # successfully anyway. -- Rob
        if len(args) != 2:
            continue

        linked_args = ['<a href="%s">%s</a>' % (data_url(arg), uri2name(arg))
                       for arg in args]
        readable_args = [uri2name(arg) for arg in args]
        if relation.startswith('/frame'):
            rendered_frame = uri2name(relation).replace('{%}', '').replace(
                '{1}', linked_args[0]).replace('{2}', linked_args[1])
            frames.append(rendered_frame)
        else:
            position = edge.get('position')
            thisNode = node['uri']
            thisNodeName = '...'
            if edge['type'] == 'relation':
                thisNode = args[0]
                otherNode = args[1]
                thisNodeName = readable_args[0]
                otherNodeName = readable_args[1]
            elif position == 1:
                otherNode = args[1]
                otherNodeName = readable_args[1]
            elif position == 2:
                otherNode = args[0]
                otherNodeName = readable_args[0]
            else:
                raise ValueError
            assertions.append({
                'position': position,
                'relation_url': data_url(relation),
                'relation': uri2name(relation),
                'relkey': "%s/%s" % (relation, position),
                'source_uri': thisNode,
                'source_url': data_url(thisNode),
                'source_text': thisNodeName,
                'target_uri': otherNode,
                'target_url': data_url(otherNode),
                'target_text': otherNodeName,
                'score': edge['score']
            })

    normalized = None

    for edge, norm_uri in conceptnet.get_outgoing_edges(uri, 'normalized'):
        name = uri2name(norm_uri)
        # cheap trick to correct for erroneous normalized edges:
        # make sure an appropriate 4 letters are the same
        for word in name.split():
            for offset in xrange(0, 5):
                if name[:4] == node['name'][offset:offset+4]:
                    normalized = {
                        'uri': norm_uri,
                        'url': data_url(norm_uri),
                        'name': uri2name(norm_uri)
                    }
                    break
    sense_list = list(conceptnet.get_incoming_edges(uri, 'senseOf',
    result_limit=100)) + list(conceptnet.get_outgoing_edges(uri, 'senseOf',
    result_limit=100))
    senses = []
    for edge, sense_uri in sense_list:
        name = uri2name(sense_uri)
        senses.append({
            'uri': sense_uri,
            'url': data_url(sense_uri),
            'name': sense_uri.split('/')[-1].replace('_', ' ')
        })

    return render_template('data.html', node=node, assertions=assertions,
            frames=frames, normalized=normalized, senses=senses)

@app.errorhandler(404)
def handler404(error):
    return render_template('404.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
