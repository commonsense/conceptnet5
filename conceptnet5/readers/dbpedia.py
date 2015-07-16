from __future__ import unicode_literals, print_function
"""
Get data from DBPedia.
"""

__author__ = 'Justin Venezuela (jven@mit.edu), Rob Speer (rspeer@mit.edu)'

from conceptnet5.language.token_utils import un_camel_case
from conceptnet5.uri import Licenses
from conceptnet5.nodes import standardized_concept_uri
from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.formats.semantic_web import NTriplesWriter, NTriplesReader, full_conceptnet_url, resource_name
import langcodes
import urllib
import sys
import re


# Python 2/3 compatibility
if sys.version_info.major >= 3:
    quote = urllib.parse.quote
    urlsplit = urllib.parse.urlsplit
    parse_url = urllib.parse.urlparse
else:
    import urlparse
    parse_url = urlparse.urlparse
    urlsplit = urlparse.urlsplit
    quote = urllib.quote


def make_surface_text(rel, start, end):
    if rel == '/r/IsA':
        return '[[{0}]] is a kind of [[{1}]]'.format(start, end)
    if rel == '/r/InstanceOf':
        return '[[{0}]] is an instance of [[{1}]]'.format(start, end)
    elif rel == '/r/PartOf':
        return '[[{0}]] is part of [[{1}]]'.format(start, end)
    elif rel == '/r/AtLocation':
        return '[[{0}]] is located in [[{1}]]'.format(start, end)
    elif rel == '/r/TranslationOf':
        return '[[{0}]] is a translation of [[{1}]]'.format(start, end)
    else:
        return '[[{0}]] {1} [[{2}]]'.format(start, rel.split('/')[-1], end)


# We're going to be building a mapping from Semantic Web URIs to ConceptNet
# URIs. This set keeps track of the ones we already used, so we don't have to
# output them again.
def parse_topic_name(text):
    """
    Get a canonical representation of a Wikipedia topic, which may include
    a disambiguation string in parentheses.

    Returns a list of URI pieces, which could be simply [name], or
    [name, pos], or [name, pos, disambiguation].
    """
    # Convert space-substitutes to spaces, and eliminate redundant spaces
    text = text.replace('_', ' ')
    while '  ' in text:
        text = text.replace('  ', ' ')
    # Find titles of the form "Topic (disambiguation)"
    match = re.match(r'([^(]+) \((.+)\)', text)
    if not match:
        return [text]
    else:
        # Assume all topics are nouns
        return [match.group(1), 'n', match.group(2).strip(' ')]


def translate_dbpedia_url(url):
    """
    Convert an object that's defined by a DBPedia URL to a ConceptNet
    URI. We do this by finding the part of the URL that names the object,
    and using that as surface text for ConceptNet.

    This is, in some ways, abusing a naming convention in the Semantic Web.
    The URL of an object doesn't have to mean anything at all. The
    human-readable name is supposed to be a string, specified by the "name"
    relation.

    The problem here is that the "name" relation is not unique in either
    direction. A URL can have many names, and the same name can refer to
    many URLs, and some of these names are the result of parsing glitches.
    The URL itself is a stable thing that we can build a ConceptNet URI from,
    on the other hand.
    """
    parsed = parse_url(url)
    domain = parsed.netloc

    if domain == 'dbpedia.org':
        # Handle old DBPedia URLs that had no language code
        lang = 'en'
    else:
        domain_parts = domain.split('.', 1)
        if domain_parts[1] == 'dbpedia.org':
            lang = domain_parts[0]

            # If we can't name this language in English, it's probably
            # not really a language.
            if langcodes.get(lang).language_name('en') == lang:
                return None
        else:
            return None

    # Some Semantic Web URLs are camel-cased. ConceptNet URIs use underscores
    # between words.
    pieces = parse_topic_name(resource_name(url))
    pieces[0] = un_camel_case(pieces[0])
    return standardized_concept_uri(lang, *pieces)


SPECIFIC_RELATION_WHITELIST = {
    'genre', 'field', 'knownFor', 'mainInterest', 'notableIdea',
    'spokenIn', 'languageFamily', 'influenced', 'influencedBy'
}

# Ban some concepts that are way too generic *and* differ from the common way that
# people use these words
CONCEPT_BLACKLIST = {
    '/c/en/work', '/c/en/agent', '/c/en/artist'
}


def map_dbpedia_relation(url):
    """
    Recognize some relations that we can extract from DBPedia, and convert
    them to ConceptNet relations. If the relation is specific to DBPedia, it'll
    be in the '/r/dbpedia' namespace.

    >>> map_dbpedia_relation('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
    '/r/InstanceOf'
    >>> map_dbpedia_relation('http://dbpedia.org/ontology/location')
    '/r/AtLocation'
    >>> map_dbpedia_relation('http://dbpedia.org/ontology/genre')
    '/r/dbpedia/genre'
    """
    name = resource_name(url)
    if name in {'type', 'occupation'}:
        return '/r/InstanceOf'
    elif name.startswith('location'):
        return '/r/AtLocation'
    elif name == 'sameAs':
        return '/r/TranslationOf'
    elif name in SPECIFIC_RELATION_WHITELIST:
        return '/r/dbpedia/%s' % name
    else:
        return None


def handle_file(filename, output_file, sw_map_file):
    reader = NTriplesReader()
    out = MsgpackStreamWriter(output_file)
    map_out = NTriplesWriter(sw_map_file)
    for line in open(filename, 'rb'):
        if not line.startswith(b'#'):
            handle_triple(line.decode('utf-8').strip(), reader, out, map_out)


def handle_triple(line, reader, out, map_out):
    subj, pred, obj, tag = reader.parse_line(line)
    if tag != 'URL':
        return

    # Ignore types of edges that we don't care about:
    #   - Homepage links
    #   - GIS features
    #   - Assertions that something "is a thing"
    #   - Anonymous nodes identified with double-underscores, such as the node
    #     "Alfred_Nobel__1", which means "Alfred Nobel's occupation, whatever
    #     it is"
    #   - Nodes that are articles named "List of X" on Wikipedia
    if (
        'foaf/0.1/homepage' in pred or '_Feature' in obj or '#Thing' in obj or
        '__' in subj or '__' in obj or 'List_of' in subj or 'List_of' in obj
        or 'Wikidata:' in obj
    ):
        return

    # We don't try to parse URIs from outside of dbpedia.org's namespace.
    if 'dbpedia.org' not in obj:
        return

    subj_concept = translate_dbpedia_url(subj)
    obj_concept = translate_dbpedia_url(obj)
    subj_text = un_camel_case(parse_topic_name(resource_name(subj))[0])
    obj_text = un_camel_case(parse_topic_name(resource_name(obj))[0])
    if subj_concept is None or obj_concept is None:
        return

    # DBPedia categorizes a lot of things as 'works', which causes unnecessary
    # ambiguity. Disregard these edges; there will almost always be a more
    # specific edge calling it a 'creative work' anyway.
    if obj_concept in CONCEPT_BLACKLIST:
        return

    rel = map_dbpedia_relation(pred)
    if rel is None:
        return

    if rel in {'/r/IsA', '/r/TranslationOf'}:
        obj_text = obj_text.lower()

    # We've successfully converted this Semantic Web triple to ConceptNet URIs.
    # Now write the results to the 'sw_map' file so others can follow this
    # mapping.
    mapped_pairs = [
        (pred, rel),
        (subj, subj_concept),
        (obj, obj_concept)
    ]
    for sw_url, conceptnet_uri in mapped_pairs:
        conceptnet_url = full_conceptnet_url(conceptnet_uri)
        map_out.write_link(conceptnet_url, sw_url)

    edge = make_edge(rel, subj_concept, obj_concept,
                     dataset='/d/dbpedia/en',
                     license=Licenses.cc_sharealike,
                     sources=['/s/dbpedia/2014'],
                     surfaceText=make_surface_text(rel, subj_text, obj_text),
                     weight=0.5)

    out.write(edge)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='N-triples file of input')
    parser.add_argument('output', help='msgpack file to output to')
    parser.add_argument('sw_map', help='An N-triples file of Semantic Web equivalences')
    args = parser.parse_args()
    handle_file(args.input, args.output, args.sw_map)


if __name__ == '__main__':
    main()
