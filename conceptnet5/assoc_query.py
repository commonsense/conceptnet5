# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from conceptnet5.query import field_match

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
        except OSError:
            raise MissingAssocSpace("The term associations could not be loaded.")

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
            for edge in finder.lookup(term, limit=limit_per_term):
                if edge['start'] != term:
                    neighbor = edge['start']
                elif edge['end'] != term:
                    neighbor = edge['end']
                else:
                    continue
                neighbor_weight = weight * edge['weight'] * 0.5
                if edge['rel'].startswith('/r/Not'):
                    neighbor_weight *= -1
                expanded.append((neighbor, neighbor_weight))

        total_weight = sum(abs(weight) for (term, weight) in expanded)
        if total_weight == 0:
            return []
        return [(term, weight / total_weight) for (term, weight) in expanded]

    def associations(self, terms, filter=None, limit=20):
        vec = assoc.vector_from_terms(self.expand_terms(terms))
        similar = assoc.terms_similar_to_vector(vec)
        similar = [
            item for item in similar if item[1] > SMALL
            and self.passes_filter(item[0], filter)
        ][:limit]
        return similar
