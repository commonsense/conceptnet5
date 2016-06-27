"""
Get data from DBPedia.
"""
from conceptnet5.language.token_utils import un_camel_case
from conceptnet5.uri import Licenses
from conceptnet5.nodes import (
    standardized_concept_uri, standardize_topic, ALL_LANGUAGES, LCODE_ALIASES
)
from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.formats.semantic_web import (
    resource_name, parse_nquads, ExternalReferenceWriter
)
import urllib
import bz2
import pathlib
from operator import itemgetter
import itertools
parse_url = urllib.parse.urlparse


RELATIONS = {
    'isPartOf': '/r/PartOf',
    'series': '/r/PartOf',
    'location': '/r/AtLocation',
    'place': '/r/AtLocation',
    'locatedInArea': '/r/AtLocation',
    'sameAs': '/r/Synonym',
    # leave out differentFrom, as it is mostly about confusable names
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
    'language': '/r/dbpedia/language',
    'languageFamily': '/r/dbpedia/languageFamily',
    'spokenIn': '/r/dbpedia/spokenIn',
    'notableIdea': '/r/dbpedia/notableIdea',
    'notableWork': '/r/dbpedia/notableWork',
    'occupation': '/r/dbpedia/occupation',
    'profession': '/r/dbpedia/occupation',
    'author': '/r/dbpedia/author',
    'writer': '/r/dbpedia/writer',
    'director': '/r/dbpedia/director',
    'producer': '/r/dbpedia/producer',
    'starring': '/r/dbpedia/starring',
    'genus': '/r/dbpedia/genus',
    'leader': '/r/dbpedia/leader',
    'associatedBand': '/r/dbpedia/associatedBand',
    'associatedMusicalArtist': '/r/dbpedia/associatedMusicalArtist',
    'bandMember': '/r/dbpedia/bandMember',
    'artist': '/r/dbpedia/artist',
    'musicalArtist': '/r/dbpedia/artist',
    'musicalBand': '/r/dbpedia/artist',
    'capital': '/r/dbpedia/capital',
    'country': '/r/dbpedia/country',
    'region': '/r/dbpedia/region',
    'era': '/r/dbpedia/era',
    'service': '/r/dbpedia/service',
    'product': '/r/dbpedia/product',
}

# Ban some concepts that are way too generic and often differ from the common
# way that people use these words
CONCEPT_BLACKLIST = {
    '/c/en/work/n', '/c/en/agent/n', '/c/en/artist/n', '/c/en/thing/n'
}

TYPE_BLACKLIST = {
    'Settlement', 'Railway Line', 'Road', 'Sports Event',
    'Olympic Event', 'Soccer Tournament', 'Election', 'Diocese',
    'Year', 'Football League Season',
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
    many URLs, and some of these names are the result of parsing glitches.
    The URL itself is a stable thing that we can build a ConceptNet URI from,
    on the other hand.
    """
    if '__' in url:
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
        uri = standardize_topic(lang, text)
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


def process_dbpedia(input_dir, output_file, refs_file):
    input_path = pathlib.Path(input_dir)
    interlang_path = input_path / 'interlanguage_links_en.tql.bz2'
    mapped_urls = interlanguage_mapping(interlang_path)

    ok_concepts = set()
    out = MsgpackStreamWriter(output_file)
    refs = ExternalReferenceWriter(refs_file)

    types_path = input_path / 'instance_types_en.tql.bz2'
    quads = parse_nquads(bz2.open(str(types_path), 'rt'))
    for subj, pred, obj, _graph in quads:
        subj_url = subj['url']
        if (
            'Category:' in subj_url or 'File:' in subj_url or
            'List_of' in subj_url or '__' in subj_url
        ):
            continue
        if subj_url in mapped_urls:
            subj_concept = translate_dbpedia_url(subj_url)
            if subj_concept:
                obj_type = un_camel_case(resource_name(obj['url']))
                if obj_type not in TYPE_BLACKLIST:
                    ok_concepts.add(subj_concept)
                    obj_concept = standardized_concept_uri('en', obj_type, 'n')
                    if obj_concept not in CONCEPT_BLACKLIST:
                        ok_concepts.add(obj_concept)
                        edge = make_edge(
                            '/r/IsA', subj_concept, obj_concept,
                            dataset='/d/dbpedia/en',
                            license=Licenses.cc_sharealike,
                            sources=[{'contributor': '/s/resource/dbpedia/2015/en'}],
                            weight=0.5
                        )
                        out.write(edge)
                    for other_url in mapped_urls[subj_url]:
                        if other_url.startswith('http://wikidata.dbpedia.org/'):
                            refs.write_link(subj_concept, other_url)
                        else:
                            other_concept = translate_dbpedia_url(other_url)
                            if other_concept:
                                refs.write_link(other_concept, other_url)
                                edge = make_edge(
                                    '/r/TranslationOf',
                                    other_concept, subj_concept,
                                    dataset='/d/dbpedia/en',
                                    license=Licenses.cc_sharealike,
                                    sources=[{'contributor': '/s/resource/dbpedia/2015/en'}],
                                    weight=0.5
                                )
                                out.write(edge)

    relations_path = input_path / 'mappingbased_objects_en.tql.bz2'
    quads = parse_nquads(bz2.open(str(relations_path), 'rt'))
    for subj, pred, obj, _graph in quads:
        subj_concept = translate_dbpedia_url(subj['url'])
        obj_concept = translate_dbpedia_url(obj['url'])
        rel_name = resource_name(pred['url'])
        if subj_concept in ok_concepts and obj_concept in ok_concepts:
            if rel_name in RELATIONS:
                rel = RELATIONS[rel_name]
                edge = make_edge(
                    rel, subj_concept, obj_concept,
                    dataset='/d/dbpedia/en',
                    license=Licenses.cc_sharealike,
                    sources=[{'contributor': '/s/resource/dbpedia/2015/en'}],
                    weight=0.5
                )

    refs.close()
    out.close()


def interlanguage_mapping(interlang_path):
    quads = parse_nquads(bz2.open(str(interlang_path), 'rt'))
    mapping = {}
    for subj, values in itertools.groupby(quads, itemgetter(0)):
        subj_url = subj['url']
        vals_list = list(values)

        # Keep nodes with at least 5 translations plus the Wikidata links
        if len(vals_list) >= 7:
            concepts = [subj_url]
            for _subj, _pred, obj, _graph in vals_list:
                url = obj['url']
                if 'www.wikidata.org' in url:
                    continue
                if url.startswith('http://wikidata.dbpedia.org/'):
                    wikidata_id = resource_name(url)

                    # Return early when we see a high-numbered Wikidata ID
                    print(wikidata_id, resource_name(subj_url))
                    if int(wikidata_id[1:]) >= 50000:
                        return mapping
                concepts.append(url)

            mapping[subj_url] = concepts


