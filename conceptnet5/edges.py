from hashlib import sha1
from conceptnet5.uri import conjunction_uri, assertion_uri, Licenses
from pprint import pprint

def make_edge(rel, start, end, dataset, license, sources,
              context='/ctx/all', surfaceText=None, weight=1.0):
    """
    Take in the information representing an edge (a justified assertion),
    and output that edge in dictionary form.

        >>> e = make_edge(rel='/r/HasProperty',
        ...               start='/c/en/fire',
        ...               end='/c/en/hot',
        ...               dataset='/d/conceptnet/4/en',
        ...               license=Licenses.cc_attribution,
        ...               sources='/and/...',
        ...               surfaceText='[[Fire]] is [[hot]]',
        ...               weight=1.0)
        >>> pprint(e)
        {'context': '/ctx/all',
         'dataset': '/d/conceptnet/4/en',
         'end': '/c/en/hot',
         'features': ['/c/en/fire /r/HasProperty -',
                      '/c/en/fire - /c/en/hot',
                      '- /r/HasProperty /c/en/hot'],
         'id': '/e/f8f1b65fa55082ef834729b63b613865a4ad44a7',
         'license': '/l/CC/By',
         'rel': '/r/HasProperty',
         'sources': '/and/...',
         'start': '/c/en/fire',
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
        sources = conjunction_uri(*sources)

    # Generate a unique ID for the edge. This is the only opaque ID
    # that appears in ConceptNet objects. You can use it as a
    # pseudo-random sort order over edges.
    edge_unique_data = [uri, context, sources]
    edge_unique = ' '.join(edge_unique_data).encode('utf-8')
    id = '/e/'+sha1(edge_unique).hexdigest()
    obj = {
        'id': id,
        'uri': uri,
        'rel': rel,
        'start': start,
        'end': end,
        'context': context,
        'dataset': dataset,
        'sources': sources,
        'features': features,
        'license': license,
        'weight': weight,
        'surfaceText': surfaceText
    }
    return obj
