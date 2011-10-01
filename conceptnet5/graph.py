# -*- coding: utf-8 -*-
from neo4jrestclient.client import GraphDatabase, Node
from conceptnet5.justify import parallel
import urllib
import re
import json

def list_to_uri_piece(lst):
    """
    Encode a list in a format suitable for a URI, by representing it in a
    form of JSON.
    """
    json_str = json.dumps(lst, ensure_ascii=False)
    json_unicode = json_str.decode('utf-8')
    return json_unicode.replace(u' ', u'')

def uri_piece_to_list(uri):
    """
    Undo the effect of `list_to_uri_piece` by decoding the string from
    JSON.
    """
    return json.loads(uri)

LUCENE_UNSAFE = re.compile(r'([-+&|!(){}\[\]^"~*?\\: ])')
def lucene_escape(text):
    """
    URIs are searchable with Lucene. This might be awesome, but it means
    that when looking them up, we have to escape out special characters by
    prepending a backslash to them.

    This should only be done inside a neo4j index.query().
    """
    # The first two backslashes are understood by the expression as a
    # literal backslash. The final \1 refers to what the expression matched.
    #
    # Fun fact: if Python didn't have raw strings, the replacement string
    # would have to be '\\\\\\1'.
    return LUCENE_UNSAFE.sub(r'\\\1', text)

def normalize_uri(uri):
    """
    Ensure that a URI is in Unicode, strip whitespace that may have crept
    in, and change spaces to underscores, creating URIs that will be
    friendlier to work with later.

    We don't worry about URL-quoting here; the client framework takes
    care of that for us.
    """
    if isinstance(uri, str):
        uri = uri.decode('utf-8')
    return uri.strip().replace(u' ', u'_')

class ConceptNetGraph(object):

    def __init__(self, url):
        """
        Create a ConceptNetGraph object, backed by a Neo4j databases at the
        given URL.
        """

        self.graph = GraphDatabase(url)
        self._node_index = self.graph.nodes.indexes['node_auto_index']
        self._edge_index = self.graph.relationships.indexes['relationship_auto_index']

    def _create_node(self, uri, properties = {}):
        """
        creates generic node object,
        parses uri, takes out args, identifies type of node and runs relevant method
        
        args:
        uri -- identifier of intended node, used in index
        properties -- (optional) properties for assertions (see assertions)
        """
        # Apply normalization to the URI here. All downstream functions can
        # assume it's normalized.

        uri = normalize_uri(uri)

        if uri.count('/') < 2:
            raise ValueError("""
            The URI %r is too short. You can't create the root or
            a type with this method.
            """ % uri) 
        
        _, type, rest = uri.split('/', 2)
        method = getattr(self, '_create_%s_node' % type)
        if method is None:
            raise ValueError("I don't know how to create type %r" % type)
        return method(uri, rest, properties)

    def _create_edge(self, type, source, target, properties = {}):
        """
        Create an edge and ensure that it is indexed by its nodes.
        """
        source = self._any_to_node(source)
        target = self._any_to_node(target)
        edge = source.relationships.create(type, target, **properties)
        edge['nodes'] = '%d-%d' % (source.id, target.id)
        return edge

    def _create_assertion_from_components(self, uri, relation, args, properties):
        """
        A helper function used in creating assertions. Given that the
        relation and args have been found or created as nodes, use them to
        create the assertion.
        """

        assertion = self.graph.node(
            type='assertion',
            uri=uri,
            score=0,
            **properties
        )
        self._create_edge("relation", assertion, relation)
        for i in xrange(len(args)):
            self._create_edge("arg", assertion, args[i], {'position': i+1})
        return assertion

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
        uri_parts = uri_piece_to_list(rest)
        rel_uri = uri_parts[0]
        arg_uris = uri_parts[1:]
        args = []
        rel = self.get_or_create_node(rel_uri)
        for arg_uri in arg_uris:
            args.append(self.get_or_create_node(arg_uri))
        assertion = self._create_assertion_from_components(uri, rel, args,
                                                           properties)

        # Set a property to keep track of whether this assertion is normalized.
        # An unnormalized ("raw") assertion has a Frame in its relation slot.
        
        if rel['type'] == 'frame':
            assertion['normalized'] = False
        else:
            assertion['normalized'] = True
        return assertion

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
            name=name,
            uri=uri,
            score=0,
            **properties
        )
    
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

        language, name = rest.split('/')
        return self.graph.node(
            type='frame',
            name=name,
            language=language,
            score=0,
            uri=uri,
            **properties
        )

    def _create_relation_node(self, uri, rest, properties):
        """
        creates relation node,                                  
        uses rest as relation name
        returns node with relation parameters

        args: 
        uri -- identifier of intended node, used in index
        rest -- relevant parts of uri needed as parameters
        properties -- (optional) properties, mainly for assertions (see assertions)        
        """

        name = rest
        return self.graph.node(
            type='relation',
            name=name,
            uri=uri,
            **properties
        )
    
    def _create_source_node(self, uri, rest, properties):
        """
        creates source node,
        used rest as name
        returns node with relation paramaters

        args:
        uri -- identifier of intended node, used in index
        rest -- relevant parts or uri needed in parameters
        properties -- (optional) properties for assertion (see assertions)
        """

        name = rest.split('/')[-1]
        return self.graph.node(
            type='source',
            name=name,
            uri=uri,
            **properties
        )

    def make_assertion_uri(self, relation_uri, arg_uri_list):
        """creates assertion uri out of component uris"""
        return '/assertion/' + list_to_uri_piece([relation_uri] + arg_uri_list)

    def make_list_uri(self, type, args):
        """Creates any list-based uri out of component uris"""
        arglist = list_to_uri_piece(args)
        return '/%s/%s' % (type, arglist)

    def get_node(self, uri):
        """
        searches for node in main index,
        returns either single Node, None or Error (for multiple results)
        """

        uri = normalize_uri(uri)
        results = self._node_index.query('uri', lucene_escape(uri))
        if len(results) == 1:
            return results[0]
        elif len(results) == 0:
            return None
        else:
            assert False, "Got multiple results for URI %r" % uri

    def find_nodes(self, pattern):
        """
        Search for all nodes whose URIs match a given wildcard pattern,
        using Lucene's wildcard syntax. Returns an iterator of the results.

        See this document for Lucene's syntax:
        http://lucene.apache.org/java/2_0_0/queryparsersyntax.html
        """
        return self._node_index.query('uri', pattern)

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

    def get_edges(self, source, target):
        """
        Get edges between `source` and `target`, specified as IDs or nodes.
        """
        source = self._any_to_id(source)
        target = self._any_to_id(target)
        return self._edge_index.query('nodes', '%d-%d' % (source, target))

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

    def _any_to_uri(self, obj):
        if isinstance(obj, Node):
            return obj['uri']
        elif isinstance(obj, basestring):
            return obj
        elif isinstance(obj, int):
            return self.get_node_by_id(obj)['uri']
        else:
            raise TypeError

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

        uri = self.make_assertion_uri(self._any_to_uri(relation),[self._any_to_uri(arg) for arg in args])
        return (self.get_node(uri) or 
        self._create_assertion_from_components(uri, _any_to_node(relation), [self._any_to_node(arg) for arg in args], properties))

    def get_or_create_concept(self, language, name):
        """
        finds or creates concept using the properties of the concept:
        language and name. convenience function.

        args:
        language -- language code ie. 'en'
        name -- name of concept ie. 'dog','fish' etc
        """
        uri = "/concept/%s/%s" % (language, name)
        return self.get_node(uri) or self._create_node(uri,{})

    def get_or_create_conjunction(self, conjuncts):
        """
        finds or creates a conjunction between nodes
        takes in conjunct arguments and returns conjuntion node
        """
        conjuncts = [self._any_to_node(c) for c in conjuncts]
        uris = [c['uri'] for c in conjuncts]
        uris.sort()
        uri = u"/conjunction/" + list_to_uri_piece(uris)
        node = self.get_node(uri)

        # Do we want to use the _create_node machinery? It doesn't quite fit.
        if node is None:
            node = self.graph.node(
                type='conjunction',
                uri=uri
            )
            inverse_sum = 0.0
            for conjunct in conjuncts:
                self.get_or_create_edge('conjunct', conjunct, node)
                if conjunct['score'] > 0 and inverse_sum is not None:
                    inverse_sum += 1./conjunct['score']
                else:
                    inverse_sum = None
            if inverse_sum is not None:
                node.score = 1./inverse_sum
        return node
    
    def get_or_create_frame(self, name):
        """
        finds of creates frame using name of frame. convenience function.

        args:
        name -- name of frame, ie. "$1 is used for $2"
        """

        uri = "/frame/%s" % name
        return self.get_node(uri) or self._create_node(uri,{})

    def get_or_create_relation(self, name):
        """
        finds or creates relation using the name of the relation.
        convenience function.

        args:
        name -- name of relation ie. 'IsA'
        """

        uri = "/concept/%s" % name
        return self.get_node(uri) or self._create_node(uri, {})

    def get_or_create_source(self, source_list):
        """
        finds or creates source using a list of the source uri components.
        convenience function.

        args:
        source_list -- list of source components ex. for '/source/contributor/omcs/bedume'
        source_list would be ['contributor','omcs','bedume']
        """

        uri = self.normalize_uri("source/" + "/".join(source_list))
        return self.get_node(uri) or self._create_node(uri, {})

    def get_args(self, assertion):
        """
        Given an assertion, get its arguments as a list.
    
        Arguments are represented in the graph as edges of type 'argument', with a property
        called 'position' that will generally either be 1 or 2. (People find 1-indexing
        intuitive in this kind of situation.)
        """
        assertion = self._any_to_node(assertion)
        edges = assertion.relationships.outgoing(types=['arg'])[:]
        edges.sort(key = lambda edge: edge['position'])
        return [edge.end for edge in edges]

    def justify(self, source, target, weight=1.0):
        """
        Add an edge that justifies (or refutes) `target` using `source`.
        The weight represents the strength of the justification, from
        -1 to 1.
        """
        edge = self.get_or_create_edge('justifies', source, target,
                                       {'weight': weight})
        self.recompute_score(target)
        return edge

    def recompute_score(self, node):
        score = 0
        for edge in node.relationships.incoming(types=['justify']):
            score += edge.start['score']
        node['score'] = score
        return score

    def derive_normalized(self, source, target, weight=1.0):
        """
        Add edges indicating that one assertion is derived from another
        through normalization.

        Also adds a justification edge, which should have a positive
        weight.
        """

        assert weight > 0
        edge = self.get_or_create_edge('normalized', source, target)
        self.justify(source, target, weight)
        for node1, node2 in zip(self.get_args(source), self.get_args(target)):
            if not (node1 == node2):
                self.get_or_create_edge('normalized', source, target)
        return edge

    def delete_node(self, obj):
        """
        This function deletes nodes safely by checking their connections
        and confirming that they are superfluous for the network. It also
        deletes conjunctions that are reliant on the assumption that 
        sources are the only things that point to conjunctions

        args:
        obj -- a uri, id or node object that is the target of the deletion
        """

        node = self._any_to_node(obj)
        delete = True
        conj_list = []
        if node['type'] == 'source':
            for rel_node in node.relationships.outgoing():
                if rel_node['type'] == 'conjunction': conj_list.append(rel_node)
        elif node['type'] != 'conjunction':
            for edge in node.relationships.incoming():
                if edge.start['type'] == 'assertion':
                    delete = False
                    break
        if delete:
            for edge in node.relationships(): edge.delete()
            for conjunction in conj_list: conjunction.delete()
            node.delete()
        else: assert False, "There are other nodes that are dependent on this node"

def get_graph():
    return ConceptNetGraph('http://tortoise.csc.media.mit.edu/db/data/')
