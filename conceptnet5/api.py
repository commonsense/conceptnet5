# -*- coding: utf-8 -*-
"""

Concept Net 5
api.py file from concepnet5 module
written by Rob Speer, Julian Chaidez
Common Sense Computing Group, Medialab
Massachusetts Institute of Technology
Fall 2011

"""

import graph
import flask
import urllib
import sys
app = flask.Flask(__name__)
concept_graph = graph.get_graph()

if len(sys.argv) == 1:
    root_url = 'http://conceptnet.media.mit.edu'
else:
    root_url = sys.argv[1]

@app.route('/data/<path:uri>')
def get_data(uri):
    """
    This function retrieves information about the desired node,
    and returns that information as a json file.
    """
    uri = '/' + uri
    print uri
    node = concept_graph.get_node(uri)
    json = {}
    json['properties']= node
    json['properties']['url'] = root_url + '/data' + json['properties']['uri']
    del json['properties']['_id']
    json['incoming'] = []
    json['outgoing'] = []
    #json['assertions'] = []
    #assertion_uris = []
    for relation in concept_graph.get_incoming_edges(node['uri']):
        json['incoming'].append(relation[0])
        json['incoming'][-1]['start_url'] = root_url + '/data' + relation[0]['start']
        del json['incoming'][-1]['_id']
        if relation[0]['type'] == 'arg':
            assertion_uris.append(relation[0]['start'])
    for relation in concept_graph.get_outgoing_edges(node['uri']):
        json['outgoing'].append(relation[0])
        json['outgoing'][-1]['end_url'] = root_url + '/data' + relation[0]['end']
        del json['outgoing'][-1]['_id']
    return flask.jsonify(json)

"""
@app.route('/search/<query>')
def search(query):

    
    This function takes a url search string and outputs a
    json list of nodes with some data and urls
    

    query = Q()
    for key, val in flask.request.args.iteritems():
        query = Q(query & Q(key, val))
    json = []
    for node in concept_graph._node_index.query(query):
        json.append(node.properties)
        json[-1]['url'] = root_url + '/data' + node['uri']
    return flask.jsonify(json)
"""

if __name__ == '__main__':
   app.run(debug=False)
