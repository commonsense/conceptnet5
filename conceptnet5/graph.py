class ConceptNetGraph(object):
    def __init__(self, url)
        self.graph = GraphDatabase(url)
        self._index = self.graph.nodes.indexes['node_auto_index']

    def _create_node(self, uri):
        if uri.count('/') < 2:
            raise ValueError("""
            The URI %r is too short. You can't create the root or
            a type with this method.
            """ % uri) 
        _, type, rest = uri.split('/', 2)
        method = getattr(self, '_create_%s_node' % type)
        if method is None:
            raise ValueError("I don't know how to create type %r" % type)
        return method(self, url, rest)

    def _create_concept_node(self, uri, rest)
        language, name = rest.split('/')
        return self.graph.node(
            type='concept',
            language=language,
            name=name,
            uri=uri
        )

    def _create_relation_node(self, uri, rest)
        rel = rest
        return self.graph.node(
            type='relation',
            name=name,
            uri=uri
        )
    
    def get_node(self, uri):
        results = self._index.query('uri', uri)
        if len(results) == 1:
            return results[0]
        else if len(results) == 0:
            return None
        else:
            assert False, "Got multiple results for URI %r" % uri

    def get_or_create_node(self, uri):
        return self.get_node(uri) or self._create_node(uri)
    

