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
import re
import sys
import simplejson
app = flask.Flask(__name__)
concept_graph = graph.get_graph()

if len(sys.argv) == 1:
    root_url = 'http://conceptnet5.media.mit.edu/data'
else:
    root_url = sys.argv[1]

no_leading_slash = ['http']
"""
request keys is a dictionary which stores a record of which request paramaters
are permitted, what their default value is, what type they should return,
what their limiting values are, and whether or not they should be ignored
in the case of a request in which they could serve as the parameter for multiple
requests in a batch.

The dictionaries for request parameters contain the following:
'request_name':{'default':__,'type':__,'upper':__,'lower':__ OR 'valid':[__],
'ignore':__]
"""
request_keys = {'get':{'default':None,'type':str,'valid':None,'ignore':False},\
        'per_page':{'default':50,'type':int,'upper':100,'lower':1,'ignore':False},
        'max_score':{'default':0.0,'type':float,'upper':None,'lower':0,'ignore':True}}

def encode_uri(uri):
    """
    Encodes uri escape symbols # and ?
    """
    uri = re.sub('\?','%3F',uri)
    return re.sub('\#','%23',uri)    

def decode_uri(uri):
    """
    Decodes uri escape symbols # and ?
    """
    uri = re.sub('%3F','\?',uri)
    return re.sub('%23','\#',uri)

def correct_uri(uri):
    """
    Corrects uri by adding slash and encoding # and ? characters if necessary
    """
    re.sub('\?','%3F',uri)
    re.sub('\#','%23',uri)
    if uri[1:5] in no_leading_slash and uri[0] == '/':
        return uri[1:]
    elif uri[:4] in no_leading_slash or uri[0] == '/':
        return uri
    else:
        return '/' + uri

def add_slash(uri):
    """
    Ensures that a slash is present in all situations where slashes are
    absolutely necessary for an address.
    """
    if uri[0] == '/':
        return uri
    else:
        return '/' + uri

def create_arg_dict(ignore_specific):
    """
    This function creates the argument dictionary out of the request dictionary
    created by flask. It ignores query specific parameters in the case of a general
    request for more than a single type of edge or node, and it allows the 
    creation of such a dictionary to be moved out of the more local request functions
    """

    args = flask.request.args
    return_args = {}
    if ignore_specific:
        for k in request_keys.keys():
            if k in args and k in request_keys:
                if request_keys[k]['ignore']: return_args[k] = request_keys[k]['default']
                else: 
                    return_args[k],error_message = check_valid(args.get(k,type=request_keys[k]['type']),k,request_keys[k])
                    if error_message != '':
                        return error_message
            else:
                return_args[k] = request_keys[k]['default']
    else:
        for k in request_keys.keys():
            if k in args:
                return_args[k],error_message = check_valid(args.get(k,type=request_keys[k]['type']),k,request_keys[k])
                if error_message != '':
                    return error_message
            else: return_args[k] = request_keys[k]['default']
    return return_args

def check_valid(arg, name, request_params):
    """
    This function confirms the validity or invalidity of a parameter as specified
    by the request_keys dict.
    """
    if type(arg) == int or type(arg) == float:
        if arg < request_params['lower'] or (arg > request_params['upper'] and request_params['upper'] != None):
            return None, 'the parameter ' + name + ' was given an invalid value.\
            Please only request values from ' + str(request_params['lower']) + ' to '\
            + str(request_params['upper']) + '.'
        else:
            return arg, ''
    elif type(arg) == str:
        if not request_params['valid'] or arg in request_params['valid']:
            return arg, ''
        else:
            return None, 'the parameter ' + name + ' was given the invalid value: ' + arg\
            + '. Please only request one of the following values: ' + ', '.join(request_params['valid'])

@app.route('/')
def see_documentation():
    """
    This function redirects to the api documentation
    """
    return flask.redirect('https://github.com/commonsense/conceptnet5/wiki/API')

@app.route('/<path:uri>/')
def get_data(uri):
    """
    This function is the primary get function which is used to return most
    json data.
    """
    json = {}
    uri = decode_uri(uri)
    if concept_graph.get_node(correct_uri(uri)) != None:
        requests = flask.request.args.get('get')
        if requests == None or len(requests.split(' ')) != 1:
            args = create_arg_dict(True)
        else:
            args = create_arg_dict(False)
        if type(args) == str:
            return flask.Response(response=flask.json.dumps({'error':args}),status=404,mimetype='json')
        if requests == None:
            for k,f_list in valid_requests.iteritems():
                for label,f in f_list.iteritems():
                    json[label] = f(uri,args)
            return flask.jsonify(json)
        else:
            requests = requests.split(' ')
            valid = True
            for i in requests:
                if i in valid_requests.keys():
                    for label,f in valid_requests[i].iteritems():
                        json[label] = f(uri,args)
                else:
                    valid = False
                    break
            if valid:
                return flask.jsonify(json)
            else:
                return flask.Response(response=flask.json.dumps({'error':'invalid request for parameter '\
                        + i + ' from uri ' + correct_uri(uri)}),status=404,mimetype='json')
    else:
        return flask.Response(response=flask.json.dumps({'error':'invalid uri ' + correct_uri(uri)}),status=404,mimetype='json')

def get_properties(uri,args):
    """
    This function retrieves parameters about the node in question.
    """
    uri = correct_uri(uri)
    if uri[0] == '/':
        identifier_uri = uri[1:]
    else:
        identifier_uri = uri
    if uri.split('/')[0] == 'assertion':
        node = concept_graph.get_node_w_score(uri)
    else:
        node = concept_graph.get_node(correct_uri(uri))
    node['url'] = root_url + encode_uri(add_slash(uri))
    del node['_id']
    return node

def get_incoming_assertions(uri,args):
    """
    This function retrieves information about which assertions point to
    the node in question. It does so in a paginated format based on max score.
    """
    json = []
    assertion_list = []
    node_score = concept_graph.get_node_w_score(correct_uri(uri))['score']
    max_score = args['max_score'] * node_score
    new_max_score = 0.0
    for relation in concept_graph.get_incoming_edges(correct_uri(uri), _type='arg', max_score=max_score, result_limit=args['per_page']):
        assertion_list.append(correct_uri(relation[1]))
        new_max_score = relation[0]['score']
    new_max_score = round(new_max_score / node_score, 19)
    for assertion in concept_graph.get_nodes_w_score(assertion_list):
        json.append(assertion)
        json[-1]['url'] = root_url  + encode_uri(add_slash(json[-1]['uri']))
        del json[-1]['_id']
    if len(json) == args['per_page']:
        json.append({})
        json[-1]['next'] = root_url + add_slash(uri)\
        + '?get=incoming_assertions'+ '&per_page=' + str(args['per_page']) + '&max_score=' + str(new_max_score)
    return json

def get_incoming_assertions_url(uri,args):
    """
    This function returns a url linking to a json page with only information
    on incoming assertions
    """
    return root_url + encode_uri(add_slash(uri)) + '?get=incoming_assertions'

def get_incoming_edges(uri,args):
    """
    This function retrieves information about the incomign edges of
    the node in question. It does so in a paginated format based on max score.
    """
    json = []
    for relation in concept_graph.get_incoming_edges(correct_uri(uri), max_score=args['max_score'], result_limit=args['per_page']):
        json.append(relation[0])
        json[-1]['start_url'] = root_url + encode_uri(add_slash(json[-1]['start']))
        try: del json[-1]['_id']
        except KeyError: pass
        del json[-1]['jitter']
    if len(json) == args['per_page']:
        json.append({})
        json[-1]['next'] = root_url + encode_uri(add_slash(uri))\
        + '?get=incoming_edges'+ '&per_page=' + str(args['per_page']) + '&max_score=' + str(json[-2]['score'])
    return json

def get_incoming_edges_url(uri,args):
    """
    This function returns a url linking to a json page with only information
    on incoming edges
    """
    return root_url + encode_uri(add_slash(uri)) + '?get=incoming_edges'

def get_outgoing_edges(uri,args):
    """
    This function retrieves information about the outgoing edges of
    the node in question. It does so in a paginated format based on max score.
    """
    json = []
    for relation in concept_graph.get_outgoing_edges(correct_uri(uri), max_score=args['max_score'], result_limit=args['per_page']):
        json.append(relation[0])
        json[-1]['end_url'] = root_url + encode_uri(add_slash(json[-1]['end']))
        try: del json[-1]['_id']
        except KeyError: pass
        del json[-1]['jitter']
    if len(json) == args['per_page']:
        json.append({})
        json[-1]['next'] = root_url + encode_uri(add_slash(uri))\
        + '?get=outgoing_edges'+ '&per_page=' + str(args['per_page']) + '&max_score=' + str(json[-2]['score'])
    return json

def get_outgoing_edges_url(uri,args):
    """
    This function returns a url linking to a json page with only information
    on outgoing edges.
    """
    return root_url + encode_uri(add_slash(uri)) + '?get=outgoing_edges'

def get_word_senses(uri,args):
    """
    This function retrieves information about the word senses related to
    the node in question. It gives all wordsenses in one go.
    It also yields all word senses of those word senses by default.
    """
    json = []
    node_list = []
    for relation in concept_graph.get_incoming_edges(correct_uri(uri), _type='senseOf'):
        node_list.append(correct_uri(relation[1]))
    for node in concept_graph.get_nodes_w_score(node_list):
        json.append(node)
        json[-1]['url'] = root_url  + encode_uri(add_slash(json[-1]['uri']))
        del json[-1]['_id']
    return json

def get_word_sense_of(uri,args):
    """
    This function retrieves information about the nodes that this node
    is a word sense of. It yields all wordsenses in one go.
    """
    json = []
    node_list = []
    for relation in concept_graph.get_outgoing_edges(correct_uri(uri), _type='senseOf'):
        node_list.append(correct_uri(relation[1]))
    for node in concept_graph.get_nodes_w_score(node_list):
        json.append(node)
        json[-1]['url'] = root_url + encode_uri(add_slash(json[-1]['uri']))
        del json[-1]['_id']
    return json

def get_normalized(uri,args):
    """
    This function retrieves information about the nodes that are normalized
    concepts of this node, if there are any.
    """
    json = []
    node_list = []
    for relation in concept_graph.get_outgoing_edges(correct_uri(uri), _type='normalized'):
        node_list.append(correct_uri(relation[1]))
    for node in concept_graph.get_nodes_w_score(node_list):
        json.append(node)
        json[-1]['url'] = root_url + encode_uri(add_slash(json[-1]['uri']))
        del json[-1]['_id']
    return json

def get_normalized_of(uri,args):
    """
    This function retrieves information about the nodes that this node is a
    normalized version of, if there are any.
    """
    json = []
    node_list = []
    for relation in concept_graph.get_incoming_edges(correct_uri(uri), _type='normalized'):
        node_list.append(correct_uri(relation[1]))
    for node in concept_graph.get_nodes_w_score(node_list):
        json.append(node)
        json[-1]['url'] = root_url + encode_uri(add_slash(json[-1]['uri']))
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
    app.run(debug=False)
