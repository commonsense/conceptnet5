import json

from nose.tools import eq_
from pyld import jsonld

from conceptnet5.api import lookup_grouped_by_feature, lookup_paginated
from conceptnet5.util import get_support_data_filename

context = None


def setUp():
    global context
    context_filename = get_support_data_filename('ld/context.ld.json')
    context = json.load(open(context_filename))


def flat_map(response):
    """
    Transform a response using JSON-LD's "flatten" operation, and return a
    dictionary mapping resources (as fully-qualified URLs) to their values
    (also containing fully-qualified URLs).
    """

    # The URL in '@context' may not be available yet, because we probably
    # haven't deployed. So replace the response's "@context" with the
    # contents of that file.
    response['@context'] = context['@context']

    # jsonld.flatten gives us a list of objects, which all have @id values
    # (unless they're awkward "blank nodes", like definitions of features).
    # The @id values are unique after flattening, so we can make a dictionary
    # keyed by them.
    result = {}
    flat_objects = jsonld.flatten(response)
    for obj in flat_objects:
        if '@id' in obj:
            result[obj['@id']] = obj
    return result


def vocab(name):
    """
    Given a property such as 'rel', get its fully-qualified URL in our
    JSON-LD vocabulary.
    """
    return "http://api.conceptnet.io/ld/conceptnet5.7/context.ld.json#" + name


def api(uri):
    """
    Given a URI that uses the ConceptNet API, such as "/c/en/test", get its
    fully-qualified URL.
    """
    return "http://api.conceptnet.io" + uri


def check_id_match(value, uri):
    """
    Check whether we got a result that matches the URI we expect it to,
    although that URI might appear in a few different forms.
    """
    if isinstance(value, list):
        # If we got a list of results, it should have 1 item, and that item
        # should be the value we're interested in
        eq_(len(value), 1)
        value = value[0]

    if isinstance(value, str):
        value_id = value
    else:
        value_id = value['@id']

    eq_(value_id, uri)


def test_lookup_paginated():
    response = lookup_paginated('/c/en/test', limit=5)

    # The original response points to a context file retrieved over HTTP.
    # Check its value before we mess with it.
    orig_context = response['@context']
    eq_(orig_context, ["http://api.conceptnet.io/ld/conceptnet5.7/context.ld.json"])

    ld = flat_map(response)

    # Look at the details of the related node "quiz"
    quiz = ld[api('/c/en/quiz')]
    check_id_match(quiz['@type'], vocab('Node'))
    quiz_label = quiz[vocab('label')][0]
    eq_(quiz_label, {'@type': 'http://www.w3.org/2001/XMLSchema#string', '@value': 'quiz'})

    edge = ld[api('/a/[/r/RelatedTo/,/c/en/test/,/c/en/quiz/]')]
    check_id_match(edge['@type'], vocab('Edge'))
    check_id_match(edge[vocab('dataset')], api('/d/verbosity'))
    check_id_match(edge[vocab('start')], api('/c/en/test'))
    check_id_match(edge[vocab('end')], api('/c/en/quiz'))
    check_id_match(edge[vocab('rel')], api('/r/RelatedTo'))
    check_id_match(edge[vocab('rel')], api('/r/RelatedTo'))
    eq_(
        edge[vocab('surfaceText')],
        [{'@type': 'http://www.w3.org/2001/XMLSchema#string',
          '@value': '[[test]] is related to [[quiz]]'}]
    )

    # The resource we actually asked for has more properties
    test = ld[api('/c/en/test')]
    eq_(len(test[vocab('edges')]), 5)

    pagination = ld[api('/c/en/test?offset=0&limit=5')]
    check_id_match(pagination['@type'], vocab('pagination-PartialCollectionView'))
    check_id_match(pagination[vocab('pagination-paginatedProperty')], vocab('edges'))
    check_id_match(pagination[vocab('pagination-nextPage')], api('/c/en/test?offset=5&limit=5'))


def test_lookup_grouped():
    response = lookup_grouped_by_feature('/c/en/test')
    ld = flat_map(response)

    # Look at the details of the related node "quiz", which should be the same
    # as they were for the non-grouped query
    quiz = ld[api('/c/en/quiz')]
    check_id_match(quiz['@type'], vocab('Node'))
    quiz_label = quiz[vocab('label')][0]
    eq_(quiz_label, {'@type': 'http://www.w3.org/2001/XMLSchema#string', '@value': 'quiz'})

    edge = ld[api('/a/[/r/RelatedTo/,/c/en/test/,/c/en/quiz/]')]
    check_id_match(edge['@type'], vocab('Edge'))
    check_id_match(edge[vocab('dataset')], api('/d/verbosity'))
    check_id_match(edge[vocab('start')], api('/c/en/test'))
    check_id_match(edge[vocab('end')], api('/c/en/quiz'))
    check_id_match(edge[vocab('rel')], api('/r/RelatedTo'))
    check_id_match(edge[vocab('rel')], api('/r/RelatedTo'))
    eq_(
        edge[vocab('surfaceText')],
        [{'@type': 'http://www.w3.org/2001/XMLSchema#string',
          '@value': '[[test]] is related to [[quiz]]'}]
    )

    # We got a bunch of features
    test = ld[api('/c/en/test')]
    assert len(test[vocab('features')]) > 5


def test_meta_context():
    # Use the JSON-LD context to understand itself
    ld = flat_map(context)

    # We get metadata about the context file
    top_level = ld[vocab('')]
    check_id_match(top_level["http://www.w3.org/2000/01/rdf-schema#seeAlso"], "http://api.conceptnet.io/docs")

    # We get RDF-ish definitions of the different properties, and comments
    rel = ld[vocab('rel')]
    check_id_match(rel["http://www.w3.org/2000/01/rdf-schema#range"], vocab('Relation'))
    comment = rel["http://www.w3.org/2000/01/rdf-schema#comment"][0]["@value"]
    assert comment.startswith("Links to the kind of relationship")
