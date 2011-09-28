# -*- coding: utf-8 -*-
from neo4jrestclient.client import GraphDatabase
import urllib

def uri_is_safe(uri):
    """
    Determines if this is a correctly-encoded URI, by checking for some
    common problems that would cause it to be incorrect.

    The output of encode_uri() should always pass uri_is_safe().
    """
    return (isinstance(uri, str) and ',' not in uri and ':' not in uri
            and ' ' not in uri and '&' not in uri)

def encode_uri(uri):
    """
    Takes in a URI and makes sure it follows our conventions:
    
    - expressed as a UTF-8 string
    - spaces are changed to underscores
    - URL-encoded, so for example a comma becomes %2C
    """
    if isinstance(uri, unicode):
        uri = uri.replace(u' ', u'_').encode('utf-8', 'replace')
    else:
        uri = uri.replace(' ', '_')
    return urllib.quote(uri)

def decode_uri(uri):
    """
    Converts a URI to readable Unicode text.
    """
    unquoted = urllib.unquote(uri).decode('utf-8', 'replace')
    return unquoted.replace('_', ' ')

class ConceptNetGraph(object):
    def __init__(self, url):

        """
        initializes ConceptNetGraph,
        creates GraphDatabase and node_index objects
           
        args:
        url -- url of neo4j database in use
        """

        self.graph = GraphDatabase(url)
        self._index = self.graph.nodes.indexes['node_auto_index']

    def _create_node(self, uri, properties):

        """
        creates generic node object,
        parses uri, takes out args, identifies type of node and runs relevant method
        
        args:
        uri -- identifier of intended node, used in index
        properties -- (optional) properties for assertions (see assertions)
        """

        if uri.count('/') < 2:
            raise ValueError("""
            The URI %r is too short. You can't create the root or
            a type with this method.
            """ % uri) 
        _, type, rest = uri.split('/', 2)
        method = getattr(self, '_create_%s_node' % type)
        if method is None:
            raise ValueError("I don't know how to create type %r" % type)
        return method(self, url, rest, properties)

    def _create_concept_node(self, uri, rest, properties):

        """
        creates concept node,
        parses rest argument for language and name
        returns node with concept parameters

        args:
        uri -- identifier of intended node, used in index
        rest -- relevant parts of uri needed as parameters
        properties -- (optional) properties for assertions (see assertions)
        """

        language, name = rest.split('/')
        return self.graph.node(
            type='concept',
            language=language,
            name=decode_uri(name),
            uri=uri
        )

    def _create_relation_node(self, uri, rest, properties):

        """
        creates relation node,                                  
        uses rest as relation name
        returns node with relation parameters

        args: 
        uri -- identifier of intended node, used in index
        rest -- relevant parts of uri needed as parameters
        properties -- (optional) properties for assertions (see assertions)        
        """

        name = rest
        return self.graph.node(
            type='relation',
            name=decode_uri(rel),
            uri=uri
        )
    
    def _create_assertion_node(self, uri, rest, properties):

        """
        creates assertion node,
        uses rest as to get relevant component uris and pull up the relevant nodes
        assigns relationships
        creates properties
        returns assertion with parameters

        args:
        uri -- identifier of intended node, used in index
        rest -- relevant parts of uri needed as parameters
        properties -- properties for assertions
        """

        rest = '/' + rest
        _,rel_uri,args_uris= rest.split('/_',2)
        arg_uris = args_uris.split('/_')
        args = []
        rel = self.get_or_create_node(rel_uri)
        for arg_uri in arg_uris: args.append(self.get_or_create_node(arg_uri))
        return self._create_assertion_w_components(uri, relation, args, properties)

    def _create_assertion_w_components(self, uri, relation, args, properties):

        """
        creates assertion node,
        assigns relationships
        creates properties
        returns assertion with parameters

        args:
        uri -- identifier of intended node, used in index
        rest -- relevant parts of uri needed as parameters
        properties -- properties for assertions                 
        """

        assertion = self.graph.node(   
            type='assertion', 
            uri=uri 
        )
        assertion.relationships.create("relation", relation)
        for i in xrange(len(args)):
            assertion.relationships.create("arg", args[i], position=i+1)
        for prop, value in properties.items():
            assertion[prop] = value
        return assertion

    def _make_assertion_uri(self, relation_uri, arg_uri_list):

        """creates assertion uri out of component uris"""

        return '/assertion/_' + relation_uri + '/_' + arg_uri_list.join('/_')

    def get_node(self, uri):

        """
        searches for node in main index,
        returns either single Node, None or Error (for multiple results)
        """

        if not uri_is_safe(uri):
            raise ValueError("This URI has unsafe characters in it. "
                             "Please use encode_uri() first.")
        results = self._index.query('uri', uri)
        if len(results) == 1:
            return results[0]
        elif len(results) == 0:
            return None
        else:
            assert False, "Got multiple results for URI %r" % uri
    
    def get_node_by_id(self, id):
        """
        Get a node by its ID in the database.
        """
        return self.g.graph.nodes[id]

    def get_or_create_node(self, uri, properties = {}):

        """
        tries to find node (by uri), or creates node if it doesn't exist

        args:
        uri -- uri for node in question
        properties -- optional properties for assertion       
        """

        return self.get_node(uri) or self._create_node(uri, properties)

    def get_or_create_assertion(self, relation, args, properties = {}):

        """
        finds or creates assertion using the components of the assertion:
        args, relation etc.

        args:
        relation -- relation node in desired assertion
        args -- argument nodes desired in assertion
        properties -- properties for assertion
        """

        uri = self._make_assertion_uri(self, relation['uri'],[arg['uri'] for arg in args])
        return self.get_node(uri) or self._create_assertion_w_components(self, relation, args, properties)

    def get_or_create_concept(self, language, name):

        uri = "/concept/%s/%s" % (language, uri_encode(name))
        

if __name__ == '__main__':
    g = ConceptNetGraph('http://new-caledonia.media.mit.edu:7474/db/data')
    a1 = g.get_or_create_node(encode_uri(u"/assertion/_/relation/IsA/_/concept/en/dog/_/concept/en/animal"))

    a2 = g.get_or_create_node(encode_uri(u"/assertion/_/relation/UsedFor/_/concept/zh_TW/枕頭/_/concept/zh_TW/睡覺"))
    
    a3 = g.get_or_create_node(encode_uri("/assertion/_/relation/IsA/_/concept/en/test_:D/_/concept/en/it works"))

    print a1['uri'], a1.id
    print a2['uri'], a2.id
    print a3['uri'], a3.id

