from __future__ import unicode_literals
from conceptnet5.uri import (assertion_uri, split_uri,
                             parse_possible_compound_uri)
import re


def make_edge(rel, start, end, dataset, license, sources,
              surfaceText=None, surfaceStart=None, surfaceEnd=None, weight=1.0):
    """
    Take in the information representing an edge (a justified assertion),
    and output that edge in dictionary form.

        >>> e = make_edge(rel='/r/HasProperty',
        ...               start='/c/en/fire',
        ...               end='/c/en/hot',
        ...               dataset='/d/conceptnet/4/en',
        ...               license=Licenses.cc_attribution,
        ...               sources=['/s/contributor/omcs/dev'],
        ...               surfaceText='[[Fire]] is [[hot]]',
        ...               weight=1.0)
        >>> pprint(e)
        {'dataset': '/d/conceptnet/4/en',
         'end': '/c/en/hot',
         'features': ['/c/en/fire /r/HasProperty -',
                      '/c/en/fire - /c/en/hot',
                      '- /r/HasProperty /c/en/hot'],
         'license': '/l/CC/By',
         'rel': '/r/HasProperty',
         'sources': [{'contributor': '/s/contributor/omcs/dev'}],
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
        source_list = sources
    else:
        raise ValueError("Got a non-list for 'sources': %r" % sources)

    source_resources = [source_uri_to_resource(source) for source in source_list]

    if surfaceStart is None or surfaceEnd is None:
        surfaceStart, surfaceEnd = extract_surface_terms(surfaceText)
    obj = {
        'uri': uri,
        'rel': rel,
        'start': start,
        'end': end,
        'dataset': dataset,
        'sources': source_resources,
        'features': features,
        'license': license,
        'weight': weight,
        'surfaceText': surfaceText,
        'surfaceStart': surfaceStart,
        'surfaceEnd': surfaceEnd
    }
    return obj


def source_uri_to_resource(uri):
    components = parse_possible_compound_uri('and', uri)
    resource = {}
    for component in components:
        uri_pieces = split_uri(component)
        if uri_pieces[1] in {'rule', 'process'}:
            resource['process'] = component
        elif uri_pieces[1] in {'activity', 'site'}:
            resource['activity'] = component
        elif uri_pieces[1] in {'contributor', 'resource'}:
            resource['contributor'] = component
        else:
            raise ValueError(component)
    return resource


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
