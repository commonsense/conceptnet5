# -*- coding: utf-8 -*-
"""

Concept Net 5
api.py file from concepnet5 module
written by Rob Speer, Julian Chaidez
Common Sense Computing Group, Medialab
Massachusetts Institute of Technology
Fall 2011

"""

import string
import flask
import urllib
import re
import sys
import json
from werkzeug.contrib.cache import SimpleCache
from metanl.english import normalize
from conceptnet5.web_interface.utils import uri2name
app = flask.Flask(__name__)

if len(sys.argv) == 1:
    root_url = 'http://conceptnet5.1.media.mit.edu/data'
else:
    root_url = sys.argv[1]

cache_dict = {
        'limit_timeout':60,
        'limit_amount':10000
        }

request_cache = SimpleCache(default_timeout = cache_dict['limit_timeout'])

no_leading_slash = ['http']
valid_params = {'row_start':0, 'row_num':10,
                'nodes':True,'score':True,
                'rel':False,'features':False,'text':False,'uri':False,
                'start':False,'end':False,'startLemmas':False, 'endLemmas':False,
                'context':False,'weight':False,'dataset':False,'soureces':False,
                'id':False,'timestamp':False }
                

def request_limit(ip_address):
    """
    This function checks the query ip address and ensures that the requests from that
    address have not passed the query limit
    """
    if request_cache.get(ip_address) > cache_dict['limit_amount']:
        return True, flask.Response(response=flask.json.dumps(\
        {'unauthorized':'rate limit violated'}),status=401,mimetype='json')
    else:
        request_cache.inc(ip_address,1)
        return False, None
#############edit
@app.route('/<path:uri>/')

def get_data(uri):
    fp = urllib.urlopen(get_link(parse_uri(uri)))
    text = fp.read()
    fp.close()
    myencoder = json.JSONDecoder()
    return json.dumps(myencoder.decode(text),indent = 2)
    
def parse_uri(uri):
    args = ()
    params = {}
    uri = uri.split(',')
    uri = [piece.split(':') for piece in uri]
    if len(uri[0]) < 2: 
        return flask.Response(response=flask.json.dumps({'error':'uri ' + str(uri)}),status=404,mimetype='json')
    else:
        if uri[0][0] == '/search':
            args = ('search',[uri2name(piece) for piece in uri[0][1].split('&')])
        elif uri[0][0] == '/path':
            args = ('path',[uri2name(uri[0][1].split('&')[0].split('=')[1]),uri2name(uri[0][1].split('&')[1].split('=')[1])])
        else: 
            return flask.Response(response=flask.json.dumps({'error':'uri ' + str(uri)}),status=404,mimetype='json')
    if len(uri) > 1:
        for param in query[1][1].split('&'):
            params[param.split('=')[0]] = param.split('=')[1]
    return [args,params]
    
def get_link(data):
    base = "http://io.csc.media.mit.edu:8983/solr/select?indent=on&version=2.2&q="

    query = ''
    if data[0][0] == 'search':
        for i in range(len(data[0][1])-1):
            query += str(data[0][1][i]) + ' AND '
        query += data[0][1][len(data[0][1])-1]
        query = urllib.quote(query,'')+'&fq='
    else:
        query = urllib.quote('start:/c/en/' + data[0][1][0] + ' end:/c/en/' + data[0][1][1])
        filt = ''
        for i in range(len(data[0][1])-1):
            filt += str(data[0][1][i]) + '* AND '
        filt += data[0][1][len(data[0][1])-1]+'*'
        query += '&fq='+urllib.quote(filt,'')

    paramlist = ''
    for param in valid_params:
        if (param != 'row_start' and param != 'row_num') and valid_params[param]:
            paramlist += str(param)+','
    paramlist = '&start='+str(valid_params['row_start'])+'&rows='+str(valid_params['row_num'])+'&fl='+urllib.quote(paramlist, '')
            
    url = base+query+paramlist+'&qt=&wt=json&explainOther=&hl.fl='
    url = '%s' % url
    return url
    
@app.route('/')
def see_documentation():
    """
    This function redirects to the api documentation
    """
    return flask.redirect('https://github.com/commonsense/conceptnet5/wiki/API')

def run_function(function,args):
    """This function takes in requests with a : preceding them and parses them as a function instead
    of a node request"""
    function = function.split(':')[1]
    uri = None
    try:
        json = {}
        for k,f in valid_requests[function].iteritems():
            json[k] = f(uri,args)
        return flask.jsonify(json)
    except KeyError:
        return flask.Response(response=flask.json.dumps({'error':'invalid function ' + function}),status=404,mimetype='json')
    except TypeError:
        return flask.Response(response=flask.json.dumps({'error':'invalid arguments'}),status=404,mimetype='json')

"""
def get_edges_between(uri, args):
    if args['start'] and args['end'] and not uri:
        json = get_edges_between_helper([], add_slash(args['start']), add_slash(args['end']))
    elif args['nodes'] and not uri:
        nodes = args['nodes'][1:-1].split(',')
        if uri: nodes[0] = uri
        if len(nodes) != 2:
            raise TypeError
        json = get_edges_between_helper([], add_slash(nodes[0]), add_slash(nodes[1]))
        json = get_edges_between_helper(json, add_slash(nodes[1]), add_slash(nodes[0]))
    elif args['start'] and uri:
        json = get_edges_between_helper([], add_slash(args['start']), add_slash(uri))
    elif args['end'] and uri:
        json  = get_edges_between_helper([], add_slash(uri), add_slash(args['end']))
    elif args['node'] and uri:
        json = get_edges_between_helper([],add_slash(uri), add_slash(args['node']))
        json = get_edges_between_helper(json,add_slash(args['node']), add_slash(uri))
    else:
        json = []
    return json
"""

@app.errorhandler(404)
def not_found(error):
    return flask.jsonify({'error':'invalid request'})

valid_requests = {'path':''}
             #,'have_assertion':{'queried_assertion':get_have_assertion}
             #,'assertions_between':{'assertions_between':get_assertions_between}

if __name__ == '__main__':
    app.run(debug = True)

