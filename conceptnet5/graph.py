# -*- coding: utf-8 -*-
from neo4jrestclient.client import GraphDatabase, Node
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
        self._node_index = self.graph.nodes.indexes['node_auto_index']
        self._edge_index = self.graph.relationships.indexes['relationship_auto_index']

    def _list_nodes_and_uris(self, input_list):

        uris = []
        nodes = []
        for index, node_uri in enumerate(input_list):
            if isinstance(node_uri,Node):
                uris.append(node_uri['uri'])
                nodes.append(node_uri)
            elif uri_is_safe(node_uri):
                uris.append(node_uri)
                nodes.append(self.get_or_create_node(node_uri))
            else:
                if index == 0: invalid = 'the relation/expression'
                else: invalid = 'argument ' + str(index)
                raise TypeError("%s is an invalid type. " %(invalid))

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
            uri= uri
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
        return self._create_assertion_from_components(uri, relation, args, properties)
    
    def _create_assertion_from_components(self, uri, relation, args, properties):
        """
        A helper function used in creating assertions. Given that the 
        relation and args have been found or created as nodes, use them to
        create the assertion.
        """
        assertion = self.graph.node(   
            type=type, 
            uri=uri
        )
        self._create_edge("relation", assertion, relation)
        for i in xrange(len(args)):
            self._create_edge("arg", assertion, args[i], {'position': i+1})
        for prop, value in properties.items():
            assertion[prop] = value
        return assertion

    def _create_assertion_expr_w_components(self, type, uri, relation_frame, args, properties):

        """
        creates assertion node,
        assigns relationships
        creates properties
        returns assertion with parameters

        args:
        uri -- identifier of intended node, used in index
        rest -- relevant parts of uri needed as parameters
        properties -- properties for assertions (see _create_assertion_node function)
        """

        #assertion = self.graph.node(   
        #    type=type, 
        #    uri=uri
        #)
        #self._create_edge("relation", assertion, relation)
        #assertion.relationships.create(relation_frame[], )
        #for i in xrange(len(args)):
        #    self._create_edge("arg", assertion, args[i], {'position': i+1})
        #for prop, value in properties.items():
        #    assertion[prop] = value
        #return assertion

    def _create_frame_node(self, uri, rest, properties):

        """
        creates frame node,
        assigns name property
        returns frame (node)

        args:
        uri -- identifier of intended node, used in index
        rest -- relevant parts of uri needed as parameters
        properties -- properties for assertions (see _create_assertion_node function)
        """

        name = rest
        return self.graph.node(
            type='frame',
            name=decode_uri(rel),
            uri= uri
        ) 

    def make_assertion_uri(self, relation_uri, arg_uri_list):

        """creates assertion uri out of component uris"""

        for uri in [relation_uri] + arg_uri_list:
            if not uri_is_safe(uri):
                raise ValueError("The URI %r has unsafe characters in it. "
                                 "Please use encode_uri() first." % uri)
        return '/assertion/_' + relation_uri + '/_' + '/_'.join(arg_uri_list)

    def get_node(self, uri):

        """
        searches for node in main index,
        returns either single Node, None or Error (for multiple results)
        """

        if not uri_is_safe(uri):
            raise ValueError("This URI has unsafe characters in it. "
                             "Please use encode_uri() first.")
        results = self._node_index.query('uri', uri)
        if len(results) == 1:
            return results[0]
        elif len(results) == 0:
            return None
        else:
            assert False, "Got multiple results for URI %r" % uri

    def get_edges(self, source, target):
        """
        Get edges between `source` and `target`, specified as IDs or nodes.
        """
        source = self._any_to_id(source)
        target = self._any_to_id(target)
        return self._edge_index.query('nodes', '%d-%d' % (source, target))

    def get_edge(self, type, source, target):
        """
        Get an existing edge between two nodes with the specified type, or None
        if it doesn't exist.
        """
        edges = self.get_edges(source, target)
        for edge in edges:
            if edge.type == type:
                return edge
        return None

    def _any_to_id(self, obj):
        if isinstance(obj, Node):
            return obj.id
        elif isinstance(obj, basestring):
            node = self.get_node(obj)
            if node is None:
                raise ValueError("Could not find node %r" % obj)
            return node.id
        elif isinstance(obj, int):
            return obj
        else:
            raise TypeError

    def _any_to_node(self, obj):
        if isinstance(obj, Node):
            return obj
        elif isinstance(obj, basestring):
            node = self.get_node(obj)
            if node is None:
                raise ValueError("Could not find node %r" % obj)
            return node
        elif isinstance(obj, int):
            return self.get_node_by_id(obj)
        else:
            raise TypeError

    def _create_edge(self, type, source, target, props):
        """
        Create an edge and ensure that it is indexed by its nodes.
        """
        source = self._any_to_node(source)
        target = self._any_to_node(target)
        edge = source.relationships.create(type, target, props)
        edge['nodes'] = '%d-%d' % (source.id, target.id)

    def get_node_by_id(self, id):
        """
        Get a node by its ID in the database.
        """
        return self.graph.nodes[id]

    def get_or_create_node(self, uri, properties = {}):
        """
        tries to find node (by uri), or creates node if it doesn't exist

        args:
        uri -- uri for node in question
        properties -- optional properties for assertion       
        """

        return self.get_node(uri) or self._create_node(uri, properties)

    def get_or_create_edge(self, type, source, target, properties = {}):
        """
        Get an edge of the specified `type` between `source` and `target`.
        If it doesn't exist, create it with the given properties.
        """
        return (self.get_edge(type, source, target) or
                self._create_edge(type, source, target, properties))

    def get_or_create_assertion(self, relation, args, properties = {}):
        """
        finds or creates assertion using the components of the assertion:
        args, relation etc. 
        can take either uri or node, gets one using the other
        convenience function.

        args:
        relation -- relation node in desired assertion
        args -- argument nodes desired in assertion
        properties -- properties for assertion
        """

        uris = []
        nodes = []
        for index, node_uri in enumerate([relation] + args):
            if isinstance(node_uri,Node):
                uris.append(node_uri['uri'])
                nodes.append(node_uri)
            elif uri_is_safe(node_uri):
                uris.append(node_uri)
                nodes.append(self.get_or_create_node(node_uri))
            else:
                if index == 0: invalid = 'relation'
                else: invalid = 'argument ' + str(index)
                raise TypeError("%s is an invalid type. " % invalid)
        uri = self.make_assertion_uri(self, uris[0],uris[1:])
        return self.get_node(uri) or self._create_assertion_from_components(self, uri, nodes[0],nodes[1:], properties)

    def get_or_create_expression(self, frame, args, properties = {}):

        """
        finds or creates expression using components of the expression:
        args, frame etc.
        can take either uri or node, gets one using the other
        convenience function.

        args:
        relation -- relation node in desired expression
        args -- argument nodes desired in expression
        properties -- properties for 
        """

        #uris = []
        #nodes = []
        #for index, node_uri in enumerate([relation] + args):   

    def get_or_create_concept(self, language, name):
        """
        finds or creates concept using the properties of the concept:
        language and name. convenience function.

        args:
        language -- language code ie. 'en'
        name -- name of concept ie. 'dog','fish' etc
        """

        uri = "/concept/%s/%s" % (language, uri_encode(name))
        return self.get_node(uri) or self._create_node(uri,{})

    def get_or_create_relation(self, name):
        """
        finds or creates relation using the name of the relation.
        convenience function.

        args:
        name -- name of relation ie. 'IsA'
        """

        uri = "/concept/%s" % (uri_encode(name))
        return self.get_node(uri) or self._create_node(uri,{})

    def get_or_create_frame(self, name):

        """
        finds of creates frame using name of frame. convenience function.

        args:
        name -- name of frame, ie. "{1} is used for {2}"
        """

        uri = "/frame/%s" % (uri_encode(name))
        return self.get_node(uri) or self._create_node(uri,{})

    #def get_args(self,assertion):
    #    """
    #    Given an assertion, get its arguments as a list.
    #
    #    Arguments are represented in the graph as edges of type 'argument', with a property
    #    called 'position' that will generally either be 1 or 2. (People find 1-indexing
    #    intuitive in this kind of situation.)
    #    """
    #
    #    if uri_is_safe(assertion): self._get_node(assertion)
    #    if node['type'] != 'assertion': 
    #    edges = assertion.relationships.outgoing(types=['arg'])[:]
    #    edges.sort(key = lambda edge: edge.properties['position'])
    #    if len(edges) > 0:
    #        assert edges[0]['position'] == 1, "Arguments of {0} are not 1-indexed".format(assertion)
    #    return [edge.end for edge in edges]


if __name__ == '__main__':
    g = ConceptNetGraph('http://localhost:7474/db/data')
    a1 = g.get_or_create_node(encode_uri(u"/assertion/_/relation/IsA/_/concept/en/dog/_/concept/en/animal"))

    a2 = g.get_or_create_node(encode_uri(u"/assertion/_/relation/UsedFor/_/concept/zh_TW/枕頭/_/concept/zh_TW/睡覺"))
    
    a3 = g.get_or_create_node(encode_uri("/assertion/_/relation/IsA/_/concept/en/test_:D/_/concept/en/it works"))

    print a1['uri'], a1.id
    print a2['uri'], a2.id
    print a3['uri'], a3.id
    print g.get_edge('justify', 0, 474).id

