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
    root_url = 'http://conceptnet.media.mit.edu/data'
else:
    root_url = sys.argv[1]

@app.route('/<path:uri>/')
def get_data(uri):
    """
    This function retrieves information about the desired node,
    and returns that information as a json file.
    TO DO: PAGINATED, TWO ELEMENT DICTIONARY
    CREATE A LINK TO FIRST ASSERTION PAGE
    PAGINATED BY SCORE
    """
    uri = '/' + uri
    #print uri
    node = concept_graph.get_node(uri)
    json = {}
    json['properties'] = node
    json['properties']['url'] = root_url + uri
    del json['properties']['_id']
    json['incoming_assertions'] = get_assertions(uri)
    json['incoming_assertions_url'] = root_url + '/incoming_assertions' + uri
    json['incoming_edges'] = get_incoming(uri)
    json['incoming_edges_url'] = root_url + '/incoming_edges' + uri
    json['outgoing_edges'] = get_outgoing(uri)
    json['outgoing_edges_url'] = root_url + '/outgoing_edges' + uri
    return flask.jsonify(json)

def get_assertions(uri, max_score = 0.0):
    """
    This function retrieves information about which assertions point to
    the node in question. It does so in a paginated format based on max score.
    TO DO: PAGINATED BY ASSERTION SCORE
    """
    json = []
    new_max_score = 0
    for relation in concept_graph.get_incoming_edges(uri, _type='arg', max_score=max_score, result_limit=50):
        json.append(concept_graph.get_node(relation[1]))
        json[-1]['url'] = root_url  + json[-1]['uri']
        del json[-1]['_id']
        new_max_score = relation[0]['score']
    if len(json) == 50:
        json.append({})
        json[-1]['next'] = root_url + '/incoming_assertions' + uri + '/' + str(new_max_score)
    return json

@app.route('/incoming_assertions/<path:uri>/', defaults={'max_score':0.0})
@app.route('/incoming_assertions/<path:uri>/<float:max_score>/')
def get_incoming_assertions(uri, max_score):
    """This function uses get_assertions and outputs json"""
    return flask.jsonify({'incoming_assertions':get_assertions('/'+uri, max_score=max_score)})

def get_incoming(uri, max_score = 0.0):
    """
    This function retrieves information about the incomign edges of
    the node in question. It does so in a paginated format based on max score.
    """
    json = []
    for relation in concept_graph.get_incoming_edges(uri, max_score=max_score, result_limit=50):
        json.append(relation[0])
        last_id = json[-1]['_id']
        del json[-1]['_id']
    if len(json) == 50:
        json.append({})
        json[-1]['next'] = root_url + '/incoming_edges' + uri + '/' + str(json[-2]['score'])
    return json

@app.route('/incoming_edges/<path:uri>/', defaults={'max_score':0.0})
@app.route('/incoming_edges/<path:uri>/<float:max_score>/')
def get_incoming_edges(uri, max_score):
    """This function uses get_incoming and outputs json"""
    return flask.jsonify({'incoming_edges':get_incoming('/'+uri, max_score=max_score)})

def get_outgoing(uri, max_score = 0.0):
    """
    This function retrieves information about the outgoing edges of
    the node in question. It does so in a paginated format based on max score.
    """
    json = []
    for relation in concept_graph.get_outgoing_edges(uri, max_score=max_score, result_limit=50):
        json.append(relation[0])
        del json[-1]['_id']
    if len(json) == 50:
        json.append({})
        json[-1]['next'] = root_url + '/outgoing_edges' + uri + '/' + str(json[-2]['score'])
    return json

@app.route('/outgoing_edges/<path:uri>/', defaults={'max_score':0.0})
@app.route('/outgoing_edges/<path:uri>/<float:max_score>/')
def get_outgoing_edges(uri, max_score):
    """This function uses get_outgoing and outputs json"""
    return flask.jsonify({'outgoing_edges':get_outgoing('/'+uri, max_score=max_score)})

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
    app.run(debug=True)
