"""
This module provides a bit of ontological information about the relations
that we support in ConceptNet. Every relation that ConceptNet supports
appears in this module.
"""


def _make_symmetric_dict(d):
    newdict = dict(d)
    for key, val in d.items():
        newdict[val] = key
    return newdict


ALL_RELATIONS = [
    "/r/Antonym",
    "/r/AtLocation",
    "/r/CapableOf",
    "/r/Causes",
    "/r/CausesDesire",
    "/r/CreatedBy",
    "/r/DefinedAs",
    "/r/DerivedFrom",
    "/r/Desires",
    "/r/DistinctFrom",
    "/r/Entails",
    "/r/EtymologicallyRelatedTo",
    "/r/ExternalURL",
    "/r/FormOf",
    "/r/HasA",
    "/r/HasContext",
    "/r/HasFirstSubevent",
    "/r/HasLastSubevent",
    "/r/HasPrerequisite",
    "/r/HasProperty",
    "/r/HasSubevent",
    "/r/InstanceOf",
    "/r/IsA",
    "/r/LocatedNear",
    "/r/MadeOf",
    "/r/MannerOf",
    "/r/MotivatedByGoal",
    "/r/NotCapableOf",
    "/r/NotDesires",
    "/r/NotHasProperty",
    "/r/NotUsedFor",
    "/r/ObstructedBy",
    "/r/PartOf",
    "/r/ReceivesAction",
    "/r/RelatedTo",
    "/r/SimilarTo",
    "/r/SymbolOf",
    "/r/Synonym",
    "/r/UsedFor",
    "/r/dbpedia/capital",
    "/r/dbpedia/field",
    "/r/dbpedia/genre",
    "/r/dbpedia/genus",
    "/r/dbpedia/influencedBy",
    "/r/dbpedia/knownFor",
    "/r/dbpedia/language",
    "/r/dbpedia/leader",
    "/r/dbpedia/occupation",
    "/r/dbpedia/product",
]

# These relations are symmetric: it doesn't matter which concept is their
# 'start' or 'end'.
SYMMETRIC_RELATIONS = {
    '/r/RelatedTo',
    '/r/SimilarTo',
    '/r/EtymologicallyRelatedTo',
    '/r/Synonym',
    '/r/Antonym',
    '/r/DistinctFrom'
}


# These relations are opposites of each other. Generally, a pair of terms
# having one relation implies that they don't have the opposite relation.
# You could consider these relations themselves to be related by the
# /r/Antonym relation.
OPPOSITE_RELATIONS = _make_symmetric_dict({
    '/r/NotDesires': '/r/Desires',
    '/r/NotUsedFor': '/r/UsedFor',
    '/r/NotCapableOf': '/r/CapableOf',
    '/r/NotHasProperty': '/r/HasProperty',
    '/r/Antonym': '/r/Synonym',
    '/r/ObstructedBy': '/r/HasPrerequisite',
})


# Most relations can be generalized into less specific relations. They don't
# form a strict tree in this way, but if you follow the chain of entailed
# relations, you'll usually get to either the very general /r/RelatedTo
# or /r/DistinctFrom.
#
# You could consider these relations themselves to be related by the
# /r/Entails relation.
#
# This mapping is not currently used in the ConceptNet code, but it could
# be used either in querying or in learning about relations.
ENTAILED_RELATIONS = {
    '/r/Antonym': '/r/DistinctFrom',

    '/r/Causes': '/r/RelatedTo',
    '/r/CausesDesire': '/r/RelatedTo',
    '/r/CapableOf': '/r/RelatedTo',
    '/r/CreatedBy': '/r/RelatedTo',
    '/r/DerivedFrom': '/r/RelatedTo',
    '/r/EtymologicallyRelatedTo': '/r/RelatedTo',
    '/r/Entails': '/r/RelatedTo',   # can we connect entailment and sub-events?
    '/r/HasContext': '/r/RelatedTo',
    '/r/HasProperty': '/r/RelatedTo',
    '/r/HasSubevent': '/r/RelatedTo',
    '/r/HasAgent': '/r/RelatedTo',
    '/r/HasTheme': '/r/RelatedTo',
    '/r/IsA': '/r/RelatedTo',
    '/r/LocatedNear': '/r/RelatedTo',
    '/r/MotivatedByGoal': '/r/RelatedTo',
    '/r/ReceivesAction': '/r/RelatedTo',
    '/r/SimilarTo': '/r/RelatedTo',
    '/r/SymbolOf': '/r/RelatedTo',
    '/r/UsedFor': '/r/RelatedTo',
    '/r/dbpedia': '/r/RelatedTo',

    '/r/FormOf': '/r/DerivedFrom',

    '/r/HasFirstSubevent': '/r/HasSubevent',
    '/r/HasLastSubevent': '/r/HasSubevent',
    '/r/HasPrerequisite': '/r/HasSubevent',

    '/r/MannerOf': '/r/Entails',

    '/r/DefinedAs': '/r/IsA',
    '/r/InstanceOf': '/r/IsA',

    '/r/AtLocation': '/r/LocatedNear',
    '/r/HasA': '/r/LocatedNear',

    '/r/PartOf': '/r/AtLocation',

    '/r/MadeOf': '/r/HasA',

    '/r/Synonym': '/r/SimilarTo',
}


def is_negative_relation(rel):
    """
    Negative relations describe ways that concepts are different or unrelated.
    In cases where we our goal is to determine how related concepts are, such
    as conceptnet5.builders.reduce_assoc, we should disregard negative
    relations.
    """
    return rel.startswith('/r/Not') or rel == '/r/Antonym' or rel == '/r/DistinctFrom'
