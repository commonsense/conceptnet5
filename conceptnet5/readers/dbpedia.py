"""
Filter data from DBPedia for inclusion in ConceptNet.

The data we use here is far from the entirety of DBPedia, which lists millions
of things that are not general knowledge, such as villages with a population of
20, individual roads, sports team rosters from a particular season, and so on.
We try to filter this information to get data that's suitable for ConceptNet.

We only extract information from the 'instance_types', 'interlanguage_links',
and 'mappingbased_objects' files, using 'page_links' as a filter.

We filter for relevant concepts in the following way:

- Use only pages whose English version is the target of at least 100 Wikipedia
  links, as seen in the 'page_links_en' file.
- Skip pages that are lists or Wikipedia internals.
- Filter out the instances of specific types, such as 'Settlement' and 'Road'.
- Use only pages that have been translated to at least 5 languages in the
  'interlanguage_links' file.
- Use only pages that have a Wikidata ID of less than 1000000. This is a crude
  heuristic, based on the fact that higher-numbered pages are likely to be
  less well known, but it lets us cut off reading the translation file early.

We extract types and certain relations from the pages that remain using the
'instance_types' and 'mappingbased_objects' files.

"""
from conceptnet5.language.token_utils import un_camel_case
from conceptnet5.uri import Licenses, uri_prefix, split_uri
from conceptnet5.nodes import standardized_concept_uri, topic_to_concept
from conceptnet5.edges import make_edge
from conceptnet5.languages import ALL_LANGUAGES, LCODE_ALIASES
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.formats.semantic_web import resource_name, parse_nquads
import urllib
import bz2
import pathlib
from operator import itemgetter
import itertools
parse_url = urllib.parse.urlparse


RELATIONS = {
    'isPartOf': '/r/PartOf',
    'series': '/r/PartOf',
    'languageFamily': '/r/PartOf',

    'location': '/r/AtLocation',
    'place': '/r/AtLocation',
    'locatedInArea': '/r/AtLocation',
    'spokenIn': '/r/AtLocation',

    # leave out differentFrom, as it is mostly about confusable names
    'sameAs': '/r/Synonym',
    'similar': '/r/SimilarTo',
    'related': '/r/RelatedTo',
    'seeAlso': '/r/RelatedTo',
    'type': '/r/InstanceOf',

    'field': '/r/dbpedia/field',
    'academicDiscipline': '/r/dbpedia/field',
    'genre': '/r/dbpedia/genre',
    'literaryGenre': '/r/dbpedia/genre',
    'influencedBy': '/r/dbpedia/influencedBy',
    'knownFor': '/r/dbpedia/knownFor',
    'notableIdea': '/r/dbpedia/knownFor',
    'notableWork': '/r/dbpedia/knownFor',
    'language': '/r/dbpedia/language',
    'occupation': '/r/dbpedia/occupation',
    'profession': '/r/dbpedia/occupation',

    #'author': '/r/dbpedia/writer',
    #'writer': '/r/dbpedia/writer',
    #'director': '/r/dbpedia/director',
    #'starring': '/r/dbpedia/starring',
    #'producer': '/r/dbpedia/producer',
    #'associatedBand': '/r/dbpedia/associatedBand',
    #'associatedMusicalArtist': '/r/dbpedia/associatedMusicalArtist',
    #'bandMember': '/r/dbpedia/bandMember',
    #'artist': '/r/dbpedia/artist',
    #'musicalArtist': '/r/dbpedia/artist',
    #'musicalBand': '/r/dbpedia/artist',

    'genus': '/r/dbpedia/genus',
    'leader': '/r/dbpedia/leader',
    'capital': '/r/dbpedia/capital',
    'service': '/r/dbpedia/product',
    'product': '/r/dbpedia/product',
}

# Ban some concepts that are way too generic and often differ from the common
# way that people use these words
CONCEPT_BLACKLIST = {
    '/c/en/work/n', '/c/en/agent/n', '/c/en/artist/n', '/c/en/thing/n'
}

TYPE_BLACKLIST = {
    'Settlement', 'Railway Line', 'Road', 'Sports Event', 'Event',
    'Olympic Event', 'Soccer Tournament', 'Election', 'Diocese',
    'Year', 'Football League Season', 'Grand Prix'
}


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
    many URLs, and some of these names are rarely used or are the result of
    parsing glitches. The URL itself is a stable thing that we can build a
    ConceptNet URI from, on the other hand.
    """
    if '__' in url or 'dbpedia.org' not in url:
        return None
    parsed = parse_url(url)
    domain = parsed.netloc
    if '.' not in domain:
        return None

    if domain == 'dbpedia.org':
        # Handle old DBPedia URLs that had no language code
        domain = 'en.dbpedia.org'

    domain_parts = domain.split('.', 1)
    if domain_parts[1] == 'dbpedia.org':
        lang = domain_parts[0]
        if lang in LCODE_ALIASES:
            lang = LCODE_ALIASES[lang]
        if lang not in ALL_LANGUAGES:
            return None
        text = resource_name(url).replace('_', ' ')
        uri = topic_to_concept(lang, text)
        if uri in CONCEPT_BLACKLIST:
            return None
        else:
            return uri
    else:
        return None


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
    if name in RELATIONS:
        return RELATIONS[name]
    else:
        return None


def get_urls_from_degree_file(in_degree_file):
    urls = set()
    for line in open(in_degree_file, encoding='utf-8'):
        line = line.strip()
        if line:
            count_str, url_str = line.split(' ', 1)
            assert url_str[0] == '<'
            assert url_str[-1] == '>'
            url = url_str[1:-1]
            urls.add(url)
    return urls


def read_concept_file(concept_file):
    concepts = set()
    for line in open(concept_file, encoding='utf-8'):
        concept = uri_prefix(line.strip())
        concepts.add(concept)
    return concepts


def process_dbpedia(input_dir, output_file, concept_file):
    """
    Read through multiple DBPedia files and output filtered assertions to
    `output_file`.
    """
    ok_concepts = read_concept_file(concept_file)

    input_path = pathlib.Path(input_dir)
    interlang_path = input_path / 'interlanguage_links_en.tql.bz2'
    mapped_urls = interlanguage_mapping(interlang_path, ok_concepts)

    out = MsgpackStreamWriter(output_file)

    types_path = input_path / 'instance_types_en.tql.bz2'
    quads = parse_nquads(bz2.open(str(types_path), 'rt'))
    for subj, pred, obj, _graph in quads:
        subj_url = subj['url']
        if (
            'Category:' in subj_url or 'File:' in subj_url or
            'List_of' in subj_url or '__' in subj_url or
            'Template:' in subj_url
        ):
            continue
        if subj_url in mapped_urls:
            subj_concept = translate_dbpedia_url(subj_url)
            obj_type = un_camel_case(resource_name(obj['url']))
            if obj_type not in TYPE_BLACKLIST:
                obj_concept = standardized_concept_uri('en', obj_type, 'n')
                if obj_concept not in CONCEPT_BLACKLIST:
                    edge = make_edge(
                        '/r/IsA', subj_concept, obj_concept,
                        dataset='/d/dbpedia/en',
                        license=Licenses.cc_sharealike,
                        sources=[{'contributor': '/s/resource/dbpedia/2015/en'}],
                        weight=0.5,
                        surfaceStart=url_to_label(subj['url']),
                        surfaceEnd=url_to_label(obj['url'])
                    )
                    out.write(edge)
                for other_url in mapped_urls[subj_url]:
                    if other_url.startswith('http://wikidata.dbpedia.org/'):
                        urledge = make_edge(
                            '/r/ExternalURL',
                            subj_concept, other_url,
                            dataset='/d/dbpedia/en',
                            license=Licenses.cc_sharealike,
                            sources=[{'contributor': '/s/resource/dbpedia/2015/en'}],
                            weight=1.0
                        )
                        out.write(urledge)
                    else:
                        other_concept = translate_dbpedia_url(other_url)
                        if other_concept:
                            urledge = make_edge(
                                '/r/ExternalURL',
                                other_concept, other_url,
                                dataset='/d/dbpedia/en',
                                license=Licenses.cc_sharealike,
                                sources=[{'contributor': '/s/resource/dbpedia/2015/en'}],
                                weight=1.0
                            )
                            out.write(urledge)
                            edge = make_edge(
                                '/r/Synonym',
                                other_concept, subj_concept,
                                dataset='/d/dbpedia/en',
                                license=Licenses.cc_sharealike,
                                sources=[{'contributor': '/s/resource/dbpedia/2015/en'}],
                                weight=0.5,
                                surfaceStart=url_to_label(other_url),
                                surfaceEnd=url_to_label(subj_url)
                            )
                            out.write(edge)

    relations_path = input_path / 'mappingbased_objects_en.tql.bz2'
    quads = parse_nquads(bz2.open(str(relations_path), 'rt'))
    for subj, pred, obj, _graph in quads:
        subj_concept = translate_dbpedia_url(subj['url'])
        obj_concept = translate_dbpedia_url(obj['url'])
        rel_name = resource_name(pred['url'])
        if (
            subj_concept and obj_concept and
            subj['url'] in mapped_urls and obj['url'] in mapped_urls
        ):
            if rel_name in RELATIONS:
                rel = RELATIONS[rel_name]
                edge = make_edge(
                    rel, subj_concept, obj_concept,
                    dataset='/d/dbpedia/en',
                    license=Licenses.cc_sharealike,
                    sources=[{'contributor': '/s/resource/dbpedia/2015/en'}],
                    weight=0.5,
                    surfaceStart=url_to_label(subj['url']),
                    surfaceEnd=url_to_label(obj['url'])
                )
                out.write(edge)

    out.close()


def url_to_label(url):
    return resource_name(url).replace('_', ' ')


def interlanguage_mapping(interlang_path, ok_concepts):
    quads = parse_nquads(bz2.open(str(interlang_path), 'rt'))
    mapping = {}
    for subj, values in itertools.groupby(quads, itemgetter(0)):
        subj_url = subj['url']
        subj_concept = translate_dbpedia_url(subj_url)
        pieces = split_uri(subj_concept)
        if len(pieces) >= 6:
            sense = pieces[5]
            if 'album' in sense or 'film' in sense or 'series' in sense or 'disambiguation' in sense or 'song' in sense or 'album' in sense or 'band' in sense:
                continue
        if uri_prefix(subj_concept) in ok_concepts:
            targets = [subj_url]

            for _subj, _pred, obj, _graph in values:
                url = obj['url']
                if 'www.wikidata.org' in url:
                    continue
                if url.startswith('http://wikidata.dbpedia.org/'):
                    wikidata_id = resource_name(url)

                    # Return early when we see a high-numbered Wikidata ID
                    if int(wikidata_id[1:]) >= 1000000:
                        return mapping
                targets.append(url)

            mapping[subj_url] = targets
    return mapping


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', help="Directory containing DBPedia files")
    parser.add_argument('output_file', help='msgpack file to output to')
    parser.add_argument('concept_file', help="Text file of concepts used elsewhere in ConceptNet")
    args = parser.parse_args()
    process_dbpedia(args.input_dir, args.output_file, args.concept_file)


if __name__ == '__main__':
    main()
