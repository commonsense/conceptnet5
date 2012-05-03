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
from flask import request
from flask import send_from_directory
from flask import url_for
from metanl.english import normalize
from conceptnet5.web_interface.utils import data_url
from conceptnet5.web_interface.utils import uri2name
from conceptnet5.web_interface.utils import get_sorted_languages

########################
# Set this flag to True when developing, False otherwise! -JVen
#
DEVELOPMENT = True
#
########################

app = Flask(__name__)

if DEVELOPMENT:
  web_route = '/web/'
else:
  web_route = '/'

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'img'), 'favicon.ico',
        mimetype='image/vnd.microsoft.icon')

@app.route('/')
def home():
    return render_template('home.html', languages=get_sorted_languages())
    
@app.route('/search', methods=['POST'])
def search():
    keyword = request.form.get('keyword')
    lang = request.form.get('language')
    keyword = normalize(keyword)
    return redirect('%sc/%s/%s' % (web_route, lang, keyword))

@app.route('/assertion/<path:uri>', methods=['GET', 'POST'])
def get_assertion(uri):
    assertion_uri = '/assertion/%s' % uri
    assertion_rel_args = conceptnet.get_rel_and_args(assertion_uri)
    if not assertion_rel_args:
        return 'Invalid assertion.'
    if request.method == 'GET':
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
        return render_template('get_assertion.html', assertion=assertion)
    elif request.method == 'POST':
        # Get inputs.
        vote = request.form.get('vote')
        # Validate.
        if not vote:
            return 'You didn\'t vote.'
        # Record.
        if vote == 'agree':
            ip_address = request.remote_addr
            # TODO(jven): store vote
            return 'Successfully voted: agree'
        elif vote == 'disagree':
            ip_address = request.remote_addr
            # TODO(jven): store vote
            return 'Successfully voted: disagree.'
        else:
            return 'Invalid vote.'

@app.route('%s<path:uri>' % web_route)
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
                'assertion_uri':assertion_uri,
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
            frames=frames, normalized=normalized, senses=senses, languages=get_sorted_languages())

@app.errorhandler(404)
def handler404(error):
    return render_template('404.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
