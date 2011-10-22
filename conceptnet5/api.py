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
import simplejson
app = flask.Flask(__name__)
concept_graph = graph.get_graph()

if len(sys.argv) == 1:
    root_url = 'http://conceptnet5.media.mit.edu/data'
else:
    root_url = sys.argv[1]

@app.route('/<path:uri>/')
def get_data(uri):
    """
    This function is the primary get function which is used to return most
    json data.
    """
    json = {}
    uri = '/' + uri
    if concept_graph.get_node(uri) != None:
        request_list = flask.request.args.get('get')
        if request_list == None:
            for k,f_list in valid_requests.iteritems():
                for label,f in f_list.iteritems():
                    json[label] = f(uri)
            return flask.jsonify(json)
        else:
            request_list = request_list.split(' ')
            valid = True
            for i in request_list:
                if i in valid_requests.keys():
                    for label,f in valid_requests[i].iteritems():
                        json[label] = f(uri)
                else:
                    valid = False
                    break
            if valid:
                return flask.jsonify(json)
            else:
                return flask.Response(response=flask.json.dumps({'error':'invalid request for parameter '\
                        + i + ' from uri ' + uri}),status=404,mimetype='json')
    else:
        return flask.Response(response=flask.json.dumps({'error':'invalid uri ' + uri}),status=404,mimetype='json')

def get_properties(uri):
    """
    This function retrieves information about the node in question.
    """
    node = concept_graph.get_node(uri)
    node['url'] = root_url + '/' + uri
    del node['_id']
    return node

def get_incoming_assertions(uri):
    """
    This function retrieves information about which assertions point to
    the node in question. It does so in a paginated format based on max score.
    """
    json = []
    max_score = flask.request.args.get('max_score',type=float)
    if max_score == None:
        max_score = 0.0
    new_max_score = 0
    for relation in concept_graph.get_incoming_edges(uri, _type='arg', max_score=max_score, result_limit=50):
        json.append(concept_graph.get_node(relation[1]))
        json[-1]['url'] = root_url  + json[-1]['uri']
        del json[-1]['_id']
        new_max_score = relation[0]['score']
    if len(json) == 50:
        json.append({})
        json[-1]['next'] = root_url + uri + '?get=incoming_assertions&max_score='+str(new_max_score)
    return json

def get_incoming_assertions_url(uri):
    """
    This function returns a url linking to a json page with only information
    on incoming assertions
    """
    return root_url + uri + '?get=incoming_assertions'

def get_incoming_edges(uri):
    """
    This function retrieves information about the incomign edges of
    the node in question. It does so in a paginated format based on max score.
    """
    json = []
    max_score = flask.request.args.get('max_score',type=float)
    if max_score == None:
        max_score = 0.0
    for relation in concept_graph.get_incoming_edges(uri, max_score=max_score, result_limit=50):
        json.append(relation[0])
        del json[-1]['_id']
        del json[-1]['jitter']
    if len(json) == 50:
        json.append({})
        json[-1]['next'] = root_url + uri + '?get=incoming_edges&max_score=' + str(json[-2]['score'])
    return json

def get_incoming_edges_url(uri):
    """
    This function returns a url linking to a json page with only information
    on incoming edges
    """
    return root_url + uri + '?get=incoming_edges'

def get_outgoing_edges(uri):
    """
    This function retrieves information about the outgoing edges of
    the node in question. It does so in a paginated format based on max score.
    """
    json = []
    max_score = flask.request.args.get('max_score',type=float)
    if max_score == None:
        max_score = 0.0
    for relation in concept_graph.get_outgoing_edges(uri, max_score=max_score, result_limit=50):
        json.append(relation[0])
        del json[-1]['_id']
        del json[-1]['jitter']
    if len(json) == 50:
        json.append({})
        json[-1]['next'] = root_url + uri + '?get=outgoing_edges&max_score=' + str(json[-2]['score'])
    return json

def get_outgoing_edges_url(uri):
    """
    This function returns a url linking to a json page with only information
    on outgoing edges.
    """
    return root_url + uri + '?get=outgoing_edges'

def get_word_senses(uri):
    """
    This function retrieves information about the word senses related to
    the node in question. It gives all wordsenses in one go.
    """
    json = []
    for relation in concept_graph.get_incoming_edges(uri, _type='senseOf'):
        json.append(concept_graph.get_node(relation[1]))
        json[-1]['url'] = root_url  + json[-1]['uri']
        del json[-1]['_id']
    return json

def get_word_sense_of(uri):
    """
    This function retrieves information about the nodes that this node
    is a word sense of. It ives all wordsenses in one go.
    """
    json = []
    for relation in concept_graph.get_outgoing_edges(uri, _type='senseOf'):
        json.append(concept_graph.get_node(relation[1]))
        json[-1]['url'] = root_url + json[-1]['uri']
        del json[-1]['_id']
    return json

def get_normalized(uri):
    """
    This function retrieves information about the nodes that are normalized
    concepts of this node, if there are any.
    """
    json = []
    for relation in concept_graph.get_outgoing_edges(uri, _type='normalized'):
        json.append(concept_graph.get_node(relation[1]))
        json[-1]['url'] = root_url + json[-1]['uri']
        del json[-1]['_id']
    return json

def get_normalized_of(uri):
    """
    This function retrieves information about the nodes that this node is a
    normalized version of, if there are any.
    """
    json = []
    for relation in concept_graph.get_incoming_edges(uri, _type='normalized'):
        json.append(concept_graph.get_node(relation[1]))
        json[-1]['url'] = root_url + json[-1]['uri']
        del json[-1]['_id']
    return json


@app.errorhandler(404)
def not_found(error):
    return flask.jsonify({'error':'invalid request'})

valid_requests = {'incoming_edges':{'incoming_edges':get_incoming_edges,\
                                    'incoming_edges_url':get_incoming_edges_url},\
             'outgoing_edges':{'outgoing_edges':get_outgoing_edges,\
                               'outgoing_edges_url':get_outgoing_edges_url},\
             'incoming_assertions':{'incoming_assertions':get_incoming_assertions,\
                                    'incoming_assertions_url':get_incoming_assertions_url},\
             'word_senses':{'word_senses':get_word_senses},\
             'properties':{'properties':get_properties},\
             'word_sense_of':{'word_sense_of':get_word_sense_of},\
             'normalized':{'normalized':get_normalized},\
             'normalized_of':{'normalized_of':get_normalized_of}}

if __name__ == '__main__':
    app.run(debug=True)
