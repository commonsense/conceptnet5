from __future__ import unicode_literals
from hashlib import sha1
from conceptnet5.uri import (conjunction_uri, assertion_uri, Licenses,
                             parse_possible_compound_uri)
from pprint import pprint
import re


def make_edge(rel, start, end, dataset, license, sources,
              context='/ctx/all', surfaceText=None,
              surfaceStart=None, surfaceEnd=None, weight=1.0):
    """
    Take in the information representing an edge (a justified assertion),
    and output that edge in dictionary form.

        >>> e = make_edge(rel='/r/HasProperty',
        ...               start='/c/en/fire',
        ...               end='/c/en/hot',
        ...               dataset='/d/conceptnet/4/en',
        ...               license=Licenses.cc_attribution,
        ...               sources='/and/[/.../]',
        ...               surfaceText='[[Fire]] is [[hot]]',
        ...               weight=1.0)
        >>> pprint(e)
        {'context': '/ctx/all',
         'dataset': '/d/conceptnet/4/en',
         'end': '/c/en/hot',
         'features': ['/c/en/fire /r/HasProperty -',
                      '/c/en/fire - /c/en/hot',
                      '- /r/HasProperty /c/en/hot'],
         'id': '/e/ee13e234ee835eabfcf7c906b358cc2229366b42',
         'license': '/l/CC/By',
         'rel': '/r/HasProperty',
         'source_uri': '/and/[/.../]',
         'sources': ['/...'],
         'start': '/c/en/fire',
         'surfaceEnd': 'hot',
         'surfaceStart': 'Fire',
         'surfaceText': '[[Fire]] is [[hot]]',
         'uri': '/a/[/r/HasProperty/,/c/en/fire/,/c/en/hot/]',
         'weight': 1.0}
    """
    features = [
        "%s %s -" % (start, rel),
        "%s - %s" % (start, end),
        "- %s %s" % (rel, end)
    ]
    uri = assertion_uri(rel, start, end)
    if isinstance(sources, list):
        source_tree = conjunction_uri(*sources)
        source_list = sources
    else:
        source_tree = sources
        source_list = parse_possible_compound_uri('or', sources)

    separate_source_lists = [
        parse_possible_compound_uri('and', source)
        for source in source_list
    ]
    flat_sources = [inner for outer in separate_source_lists
                          for inner in outer]
    flat_sources = sorted(set(flat_sources))

    # Generate a unique ID for the edge. This is the only opaque ID
    # that appears in ConceptNet objects. You can use it as a
    # pseudo-random sort order over edges.
    edge_unique_data = [uri, context, source_tree]
    edge_unique = ' '.join(edge_unique_data).encode('utf-8')
    id = '/e/'+sha1(edge_unique).hexdigest()
    if surfaceStart is None or surfaceEnd is None:
        surfaceStart, surfaceEnd = extract_surface_terms(surfaceText)
    obj = {
        'id': id,
        'uri': uri,
        'rel': rel,
        'start': start,
        'end': end,
        'context': context,
        'dataset': dataset,
        'sources': flat_sources,
        'source_uri': source_tree,
        'features': features,
        'license': license,
        'weight': weight,
        'surfaceText': surfaceText,
        'surfaceStart': surfaceStart,
        'surfaceEnd': surfaceEnd
    }
    return obj


SURFACE_FORM_PATTERN = re.compile(r'\[\[(.*?)\]\]')


def extract_surface_terms(surface):
    """
    Some formats don't have separate slots for the surface text of the
    'start' and 'end' terms; we only record them as part of the overall
    surface text, in double brackets.

    A typical surface text will look like this:

        [[A dog]] has [[a tail]].

    Occasionally, there will be sentence frames that put the 'end' term
    before the 'start' term. These are marked with an asterisk.

        *[[A tail]] can belong to [[a dog]].

    This function returns the terms in their proper order -- 'surfaceStart'
    followed by 'surfaceEnd' -- so they can be indexed in the more flexible
    jsons and msgpack formats.
    """
    if not surface:
        return (None, None)
    surface_terms = SURFACE_FORM_PATTERN.findall(surface)
    if len(surface_terms) != 2:
        return (None, None)
    if surface.startswith('*'):
        surface_terms = surface_terms[::-1]
    return surface_terms
