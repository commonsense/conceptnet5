from conceptnet5.query import field_match, AssertionFinder
from conceptnet5.util import get_data_filename
from conceptnet5.vectors.formats import load_hdf
from conceptnet5.vectors import similar_to_vec, weighted_average
from conceptnet5.language.lemmatize import DBLemmatizer, LEMMA_FILENAME
import pandas as pd
import numpy as np

# Magnitudes smaller than this tell us that we didn't find anything meaningful
SMALL = 1e-6


class MissingVectorSpace(Exception):
    pass


class VectorSpaceWrapper(object):
    """
    An object that wraps the data necessary to look up vectors for terms
    (in the vector space named Conceptnet Numberbatch) and find related terms.

    The filenames usually don't need to be specified, because the system will
    look in default locations for them. They can be specified to replace them
    with toy versions for testing.
    """
    def __init__(self, vector_filename=None,
                 index_filename=None,
                 edge_filename=None,
                 lemma_filename=None):
        self.vector_filename = vector_filename or get_data_filename('vectors/numberbatch-1606.h5')
        self.index_filename = index_filename
        self.edge_filename = edge_filename
        self.lemma_filename = lemma_filename or LEMMA_FILENAME
        self.frame = None
        self.small_frame = None
        self.k = None
        self.small_k = None
        self.finder = None

    def load(self):
        """
        Ensure that all the data is loaded.
        """
        if self.frame is not None:
            return
        try:
            self.frame = load_hdf(self.vector_filename)
            self.k = self.frame.shape[1]
            self.small_k = self.k // 4
            self.small_frame = self.frame.iloc[:, :self.small_k]
        except OSError:
            raise MissingVectorSpace(
                "Couldn't load the vector space %r. Do you need to build or "
                "download it?" % self.path
            )
        self.finder = AssertionFinder(self.index_filename, self.edge_filename)
        self.lemmatizer = DBLemmatizer(self.lemma_filename)

    @staticmethod
    def passes_filter(label, filter):
        if filter is None:
            return True
        else:
            return field_match(label, filter)

    def expand_terms(self, terms, limit_per_term=10):
        """
        Given a list of weighted terms as (term, weight) tuples, add terms that
        are one step away in ConceptNet at a lower weight.

        This helps increase the recall power of the AssocSpace, because it
        means you can find terms that are too infrequent to have their own
        vector by looking up their neighbors. This forms a reasonable
        approximation of the vector an infrequent term would have anyway.
        """
        self.load()
        expanded = terms[:]
        for term, weight in terms:
            if not list(self.finder.lookup(term, limit=1)):
                term = self.lemmatizer.lemmatize_uri(term)
            for edge in self.finder.lookup(term, limit=limit_per_term):
                if field_match(edge['start'], term) and not field_match(edge['end'], term):
                    neighbor = edge['end']
                elif field_match(edge['end'], term) and not field_match(edge['start'], term):
                    neighbor = edge['start']
                else:
                    continue
                neighbor_weight = weight * min(10, edge['weight']) * 0.001
                expanded.append((neighbor, neighbor_weight))

        total_weight = sum(weight for term, weight in expanded)
        if total_weight == 0:
            return []
        else:
            return [(term, weight / total_weight) for (term, weight) in expanded]

    def expanded_vector(self, terms, limit_per_term=10):
        self.load()
        return weighted_average(self.frame, self.expand_terms(terms, limit_per_term))

    def similar_terms(self, terms, filter=None, limit=20):
        """
        Get a
        """
        if isinstance(terms, str):
            terms = [(terms, 1.)]
        # TODO: filter
        self.load()
        vec = self.expanded_vector(terms)
        small_vec = vec.iloc[:self.small_k]
        similar_sloppy = similar_to_vec(self.small_frame, small_vec, num=limit * 50)
        similar_choices = self.frame.loc[similar_sloppy.index]
        similar = similar_to_vec(similar_choices, vec, num=limit)
        return similar
