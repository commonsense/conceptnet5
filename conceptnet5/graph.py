
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
            name=name,
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
            name=name,
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
        arg_uris = arg_uris.split('/_')
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
        assertion.relationships.create("relation", rel)
        for i in xrange(len(args)):
            assertion.relationships.create("arg", args[i], position=i+1)
        for prop, value in properties.items():
            assertion[prop] = value
        return assertion

    def _make_assertion_uri(self, relation_uri, arg_uri_list):
        return '/assertion/_' + relation_uri + '/_' + arg_uri_list.join('/_')

    def get_node(self, uri):
        results = self._index.query('uri', uri)
        if len(results) == 1:
            return results[0]
        else if len(results) == 0:
            return None
        else:
            assert False, "Got multiple results for URI %r" % uri

    def get_or_create_node(self, uri, properties = {}):
        return self.get_node(uri) or self._create_node(uri, properties)

    def get_or_create_assertion(self, relation, args, properties = {}):
        uri = self._make_assertion_uri(self, relation['uri'],[arg['uri'] for arg in args])
        return self.get_node(uri) or self._create_assertion_w_components(self, relation, args, properties)


