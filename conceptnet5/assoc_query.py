# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from conceptnet5.query import field_match, AssertionFinder
from conceptnet5.util import get_data_filename


# Magnitudes smaller than this tell us that we didn't find anything meaningful
SMALL = 1e-6


class MissingAssocSpace(Exception):
    pass


class AssocSpaceWrapper(object):
    def __init__(self, path, finder):
        self.path = path
        self.finder = finder
        self.assoc = None

    def load(self):
        if self.assoc is not None:
            return

        try:
            from assoc_space import AssocSpace
            self.assoc = AssocSpace.load_dir(self.path)
        except ImportError:
            raise MissingAssocSpace("The assoc_space package is not installed.")
        except ZeroDivisionError:
            raise MissingAssocSpace("The space of term associations could not "
                                    "be loaded.")

    @staticmethod
    def passes_filter(label, filter):
        if filter is None:
            return True
        else:
            return field_match(label, filter)

    def expand_terms(self, terms, limit_per_term=10):
        """
        Given a list of weighted terms, add terms that are one step away in
        ConceptNet at a lower weight.

        This helps increase the recall power of the AssocSpace, because it
        means you can find terms that are too infrequent to have their own
        vector by looking up their neighbors. This forms a reasonable
        approximation of the vector an infrequent term would have anyway.
        """
        self.load()
        expanded = terms[:]
        for term, weight in terms:
            for edge in self.finder.lookup(term, limit=limit_per_term):
                if field_match(edge['start'], term):
                    neighbor = edge['end']
                elif field_match(edge['end'], term):
                    neighbor = edge['start']
                else:
                    continue
                neighbor_weight = weight * min(10, edge['weight']) * 0.001
                if edge['rel'].startswith('/r/Not'):
                    neighbor_weight *= -1
                expanded.append((neighbor, neighbor_weight))

        total_weight = sum(abs(weight) for (term, weight) in expanded)
        if total_weight == 0:
            return []
        return [(term, weight / total_weight) for (term, weight) in expanded]

    def expanded_vector(self, terms, limit_per_term=10):
        self.load()
        return self.assoc.vector_from_terms(self.expand_terms(terms, limit_per_term))

    def associations(self, terms, filter=None, limit=20):
        self.load()
        vec = self.expanded_vector(terms)
        similar = self.assoc.terms_similar_to_vector(vec, num=None)
        similar = [
            item for item in similar if item[1] > SMALL
            and self.passes_filter(item[0], filter)
        ][:limit]
        return similar


def get_assoc_data(name):
    finder = AssertionFinder()
    assoc_wrapper = AssocSpaceWrapper(
        get_data_filename('assoc/%s' % name), finder
    )
    return finder, assoc_wrapper
