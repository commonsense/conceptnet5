"""
Concept Net 5
cn5_webapi_client.py file from concepnet5 module
written by Rob Speer, Julian Chaidez
Digital Intuition Group, Medialab
Massachusetts Institute of Technology
Fall 2011
"""

import urllib
import json

__version__ = .10
__author__ = ['Julian Chaidez (jchaidez@mit.edu)']
VALID_GET_CALLS = [
        'properties','incoming_assertions','incoming_edges','outgoing_edges','word_senses','is_word_sense_of',
        'normalized','is_normalized_of','contexts','is_context_of','edges_between'
        ]

def query_encode(data):
    """
    Encodes the data input into the proper query format
    """
    if type(data) == list:
        return_str = ''
        for i in data:
            return_str = return_str + '+' + urllib.quote(i)
    elif type(data) == str:
        return_str == urllib.quote(data)
    elif type(data) == int or type(data) == float:
        return_str = str(data)
    else:
        return_str = urllib.quote(str(data))

def ensure_slash(uri):
    """
    Encodes a slash to a uri if that uri does not contain a leading slash
    """
    if uri[0] != '/': return '/' + uri
    else: return uri

class ConceptNetGraph(object):
    """
    This is the object through which the graph can be queried and accessed in a
    manner independent from any particular node or edge. It can be used for
    queries and get calls etc.
    """

    def __init__(self, database_url):
        """
        Initializes object by assigning a target url (a 'root')
        args:
        database_url - the base url that will be adopted as the root url
        for all calls. This will default to 'http://conceptnet5.media.mit.edu/data'
        """

        self.root = database_url
        self.valid_get_calls = VALID_GET_CALLS
        #self.valid_get_calls = json.loads(urllib.urlopen(self.root + '/valid_get_calls').read())

    def get_node(self, uri):
        """fetches node with given uri""" 
        return _base_node(self,uri) 

    def get_nodes(self, uri_list):
        """fetches a series of nodes given a list of uris"""
        nodes = json.loads(urllib.urlopen(self.root + '/' + str(uri_list).read())
        return_dict = {}
        for node in nodes['nodes']:
            return_dict[uri] = _base_node(self,node['uri'],properties = node)
        return return_dict

    def find_node(self, properties):
        pass

    def edges_between(self, uri1, uri2):
        """determines if these nodes are connected by any edges, returns those edges or and empty list if they aren't connected"""
        edges = json.loads(urllib.urlopen(self.root + '/:edges_between/?nodes=[' + uri1 + ',' + uri2 + ']').read())
        return_edges_list = []
        for i in edges['edges_between']:
            return_edges_list.append(_base_edge(self,i))
        return return_edges_list


#    def have_assertion(self, uri_list, relation):
#        """determines if a list of nodes have an assertion between it's members, returns
#        assertion or list of assertions if there are any assertions fitting the parameters"""
#        assertions = json.loads(urllib.urlopen(self.root + '/:have_assertion/?nodes=[' + uri_list.join(',') + ']&relation=' + relation
#        return_nodes_list = []
#        for node in assertions['have_assertion']:
#            return_nodes_list.append(_base_node(self, node['uri'],properties = node)
#        return return_nodes_list 

#    def assertions_between(self, uri1, uri2):
#        """retrieves all assertions between two nodes"""
#        assertions = json.loads(urllib.urlopen(self.root + '/:get_assertions/?nodes=[' + uri_list.join(',') + ']'
#        return_nodes_list = []
#        for node in assertions['assertions_between']:
#            return_nodes_list.append(_base_node(self, node['uri'], properties = node)
#        return return_nodes_list


class _query(object):
    """
    This is a container for the different types of get call functions necessary in each
    node
    """

    def __init__(self, node, call):
        """
        Initializes object by creating a custom query with all of the data necessary to make a particular call
        args:
        graph - the graph object which is associated with the database which this query will be using
        call - the call type. ex. 'outgoing_assertions'
        """

        self.call = call
        self.url = node.root + node.uri + '?get=' + call
        self.node = node
        self.cached = False
        self.cache = None

    def _get(self, refresh = False, **kwargs):
        """
        Makes a get call using args provided.
        args:
        **kwargs - the parameters that are provided for teh query
        ex. per_page = 20, max_score = 1000
        """
        if not self.cached or refresh:
            call_url = self.url
            for k,i in kwargs.iteritems():
                call.url = call.url + '&' + k + '=' + query_encode(i)
            return_dict = json.loads(urllib.urlopen(call_url).read())
            if self.call == 'properties':
                self.cache = return_dict['properties']
            else:
                self.cache = _result(self, return_dict, call_url)
            self.cached = True
        return self.cache

class _result(object):
    """
    This is a container for the results of a get call. It is essentially an iterator/index, but it
    has a handful of properties useful specifically in the context of get results
    """

    def __len__(self):
        """
        Returns number of items contained in the result
        """
        return len(self._contents)

    def __getitem__(self,key):
        """
        Returns item from results
        """
        return self._contents[key]

    def __iter__(self):
        """
        Returns self as an iterator over contents
        """
        return self

    def next(self):
        """
        Used in iterator, iterates through contents and adds to them if necessary
        """
        if self._current_item = len(self._contents):
            self.next_page()
            if self._current_item = len(self._contents):
                raise StopIteration
            else:
                self._current_item += 1
                return self._contents[self._current_item - 1]
        else:
            self._current_item += 1
            return self._contents[self._current_item - 1]

    def __init__(self, call_object, data, call_url):
        """
        Initializes object by creating all necessary indices and organizing data
        args:
        node - the node which this data is associated with
        data - the data ( a dictionary or list) returned by the query
        """

        self.node = call_object.node
        self.type = call_object.call
        self.url = call_url
        self.pages = []
        self._contents = data[self.type]
        self.general_url = data.get(self.type + '_url', None)
        if 'next' in self._contents:
            self.next_url = self._contents['next']
            del self._contents['next']
        else:
            self.next_url = None
        self.pages.append(data[self.type])
        self._current_page = 0
        self._current_item = 0

    def next_page(self):
        """
        calls the next page of data and caches old data. Circulates if already gone around.
        """
        if self._next_url:
            if len(self.pages) == self._current_page + 1:
                data = json.loads(urllib.urlopen(self.next_url).read())
                self._contents = data[self.type]
                self.pages.append(data[self.type])
            else:
                self._contents = self.pages[self._current_page + 1]
            self._current_page += 1
        if 'next' in self._contents:
            self.next_url = self._contents['next']
            del self._contents['next']
        else:
            self.next_url = None

class _base_node(object):
    """
    This is the base class from which all types of nodes will be derived.
    """

    def __getitem__(self,key):
        """
        retrieves an attribute and returns it
        """
        return getattr(self, key, None)

    def _make_call(self, call, **kwargs):
        """
        Makes arbitrary (valid) get call to the database
        args:
        call - the get call type. ex. 'incoming_assertions'
        kwargs - a dictionary of parameters for the call
        ex. {'per_page':20}
        """

        self.get[call]

    def __init__(self, graph, uri, properties = None):
        """
        Initializes object, by assigning properties and assigning the parent graph.
        args:
        graph - the graph object that is associated with the graph that this node is in
        uri - the resource identifier of this node. ex. '/concept/en/dog'
        properties - properties that can be used to initialize nodes without accessing the graph individually
        """
        self.root = graph.root
        if not properties:
            properties = json_dict = json.loads(urllib.urlopen(self.root + uri + '?get=properties').read())['properties']
        for k,i in properties.iteritems():
            setattr(self,k,i)
        self._queries = {}
        for i in graph.valid_get_calls:
            self._queries[i] = _query(self,i)
        for k,i in self._queries.iteritems():
            setattr(self,k,i._get)


class _base_edge(object):
    """
    This is the base class form which all types of edges will be derived.
    """

    def __init__(self, graph, properties):
        """
        Initializes object, assignes properties and parent graph
        args:
        graph - the graph object that is associated with the graph that this edge is in
        properties - the properties used to initialize the edge
        """
        self.root = graph.root
        for k,i in properties.iteritems():
            setattr(self,k,i)
