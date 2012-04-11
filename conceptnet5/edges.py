from conceptnet5.nodes import list_to_uri_piece, uri_piece_to_list, make_assertion_uri, normalize_uri, normalize_arbitrary_text, concept_to_lemmas
from hashlib import sha1
import json, os

def make_edge(rel, startText, startLang, endText, endLang,
              dataset, license, sources, surfaceText=None,
              weight=1.0):
    """
    Take in the information representing an edge (a justified assertion),
    and output that edge in dictionary from.
    """
    start = normalize_arbitrary_text(startText, startLang)
    end = normalize_arbitrary_text(endText, endLang)
    features = [
        "%s %s -" % (start, rel),
        "%s - %s" % (start, end),
        "- %s %s" % (rel, end)
    ]
    uri = make_assertion_uri(rel, [start, end], short=True)
    edge_unique = (uri+'|'+('|'.join(sources))).encode('utf-8')
    id = '/e/'+sha1(edge_unique).hexdigest()
    obj = {
        'id': id,
        'uri': uri,
        'rel': rel,
        'start': start,
        'end': end,
        'dataset': dataset,
        'sources': sources,
        'features': features,
        'weight': weight
    }
    return obj

class FlatEdgeWriter(object):
    """
    This class and its subclasses give you objects you can use to write
    ConceptNet 5 data structures to files. These files can then be imported
    into databases that allow you to search them.

    The default behavior is simply to write the JSON data to a file, one entry
    per line, without any additional indexing information.
    """
    def __init__(self, filename):
        self.filename = filename
        self.open = True
        self.out = open(filename, 'w')

    def write_header(self):
        pass

    def write_footer(self):
        pass

    def write(self, edge):
        line = json.dumps(edge)
        print >> self.out, line

    def close(self):
        self.write_footer()
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
        print >> self.out, '  commit: {},'
        print >> self.out, '}'
    
    def write_edge(self, edge):
        edge = dict(edge)
        startLemmas = concept_to_lemmas(edge['start'])
        endLemmas = concept_to_lemmas(edge['end'])
        relLemmas = concept_to_lemmas(edge['rel'])

        edge['startLemmas'] = startLemmas
        edge['endLemmas'] = endLemmas
        if relLemmas:
            edge['relLemmas'] = relLemmas

        json_struct = json.dumps(edge, indent=2)
        self.out.write(json_struct[2:-2]+',\n')

class MultiWriter(object):
    def __init__(self, basename):
        self.flat_writer = FlatEdgeWriter('data/flat/%s.json' % basename)
        self.solr_writer = SolrEdgeWriter('data/solr/%s.json' % basename)
        self.writers = [self.flat_writer, self.solr_writer]
        self.open = True

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

