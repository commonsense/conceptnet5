import json

class FlatEdgeWriter(object):
    """
    This class and its subclasses give you objects you can use to write
    ConceptNet 5 data structures to files. These files can then be imported
    into databases that allow you to search them.

    The default behavior is simply to write the JSON data to a file, one entry
    per line, without any additional indexing information.
    """
    def __init__(self, file):
        self.filename = None
        if isinstance(file, basestring):
            self.out = open(file, 'w')
            self.filename = file
        else:
            self.out = file
        self.open = True
        self.write_header()

    def write_header(self):
        pass

    def write_footer(self):
        pass

    def write(self, edge):
        line = json.dumps(edge)
        print >> self.out, line

    def close(self):
        self.write_footer()
        if self.filename is not None:
            self.out.close()
        self.open = False

class SolrEdgeWriter(FlatEdgeWriter):
    """
    Write a JSON dictionary with a repeated 'add' key, once for each edge,
    and a 'commit' key at the end. This is a format that Solr is good at
    importing.
    """
    def write_header(self):
        print >> self.out, '{'

    def write_footer(self):
        print >> self.out, '  "commit": {}'
        print >> self.out, '}'
    
    def write(self, edge):
        edge = dict(edge)
        if 'surfaceText' in edge and edge['surfaceText'] is None:
            del edge['surfaceText']

        json_struct = json.dumps({'add': {'doc': edge, 'boost': abs(edge['weight'])}}, indent=2)
        self.out.write(json_struct[2:-2]+',\n')

class MultiWriter(object):
    def __init__(self, basename, flat_dir='data/flat', solr_dir='data/solr', isTest=False):
        flat_file_path = '%s/%s.json' % (flat_dir, basename)
        solr_file_path = '%s/%s.json' % (solr_dir, basename)

        if isTest:
            flat_file_path = 'data/flat_test/%s.json' % basename
            solr_file_path = 'data/solr_test/%s.json' % basename

        self.flat_writer = FlatEdgeWriter(flat_file_path)
        self.solr_writer = SolrEdgeWriter(solr_file_path)
        self.writers = [self.flat_writer, self.solr_writer]
        self.open = True
        self.write_header()

    def write_header(self):
        for writer in self.writers:
            writer.write_header()
    
    def write_footer(self):
        # handled by .close()
        pass

    def close(self):
        for writer in self.writers:
            writer.close()
        self.open = False

    def write(self, edge):
        for writer in self.writers:
            writer.write(edge)

    def __del__(self):
        if self.open:
            self.close()

