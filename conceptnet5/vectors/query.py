from conceptnet5.util import get_data_filename
from conceptnet5.vectors.formats import load_hdf
from conceptnet5.vectors import (
    similar_to_vec, weighted_average, normalize_vec, cosine_similarity,
    standardized_uri
)
from conceptnet5.vectors.transforms import l2_normalize_rows
from conceptnet5.db.query import AssertionFinder
from conceptnet5.uri import uri_prefix
import wordfreq
import pandas as pd

# Magnitudes smaller than this tell us that we didn't find anything meaningful
SMALL = 1e-6


class MissingVectorSpace(Exception):
    pass


def field_match(value, query):
    """
    Determines whether a given field of an edge (or, in particular, an
    assertion) matches the given query.
    If the query is a URI, it will match prefixes of longer URIs, unless
    `/.` is added to the end of the query.
    For example, `/c/en/dog` will match assertions about `/c/en/dog/n/animal`,
    but `/c/en/dog/.` will only match assertions about `/c/en/dog`.
    """
    query = query.rstrip('/')
    if isinstance(value, list):
        return any(field_match(subval, query) for subval in value)
    elif query.endswith('/.'):
        return value == query[:-2]
    else:
        return (value[:len(query)] == query
                and (len(value) == len(query) or value[len(query)] == '/'))


class VectorSpaceWrapper(object):
    """
    An object that wraps the data necessary to look up vectors for terms
    (in the vector space named Conceptnet Numberbatch) and find related terms.

    The filenames usually don't need to be specified, because the system will
    look in default locations for them. They can be specified to replace them
    with toy versions for testing.
    """
    def __init__(self, vector_filename=None, frame=None, use_db=True):
        if frame is None:
            self.frame = None
            self.vector_filename = vector_filename or get_data_filename('vectors/mini.h5')
        else:
            self.frame = frame
            self.vector_filename = None
        self.small_frame = None
        self.k = None
        self.small_k = None
        self.finder = None
        self.standardized = None
        if use_db:
            self.finder = AssertionFinder()

    def load(self):
        """
        Ensure that all the data is loaded.
        """
        if self.small_frame is not None:
            return
        try:
            if self.frame is None:
                self.frame = load_hdf(self.vector_filename)

            if self.frame.index[0].startswith('/c/'):
                self.standardized = True
            else:
                # These terms weren't in ConceptNet standard form. Assume
                # they're in English, and stick the English language tag on
                # them without any further transformation, so we can be sure
                # we're evaluating the vectors as provided.
                self.standardized = False
                self.finder = None
                self.frame.index = [
                    '/c/en/' + label
                    for label in self.frame.index
                ]

            self.k = self.frame.shape[1]
            self.small_k = 100
            self.small_frame = self.frame.iloc[:, :self.small_k].copy()
        except OSError:
            raise MissingVectorSpace(
                "Couldn't load the vector space %r. Do you need to build or "
                "download it?" % self.vector_filename
            )

    @staticmethod
    def passes_filter(label, filter):
        if filter is None:
            return True
        else:
            return field_match(label, filter)

    def expand_terms(self, terms, limit_per_term=10, include_neighbors=True):
        """
        Given a list of weighted terms as (term, weight) tuples, add terms that
        are one step away in ConceptNet at a lower weight.

        This helps increase the recall power of the vector space, because it
        means you can find terms that are too infrequent to have their own
        vector by looking up their neighbors. This forms a reasonable
        approximation of the vector an infrequent term would have anyway.
        """
        self.load()
        expanded = terms[:]
        for term, weight in terms:
            expanded.append((term, weight / 10))
            if include_neighbors and term not in self.frame.index and self.finder is not None:
                for edge in self.finder.lookup(term, limit=limit_per_term):
                    if field_match(edge['start']['term'], term) and not field_match(edge['end']['term'], term):
                        neighbor = edge['end']['term']
                    elif field_match(edge['end']['term'], term) and not field_match(edge['start']['term'], term):
                        neighbor = edge['start']['term']
                    else:
                        continue
                    neighbor_weight = weight * min(10, edge['weight']) * 0.001
                    expanded.append((neighbor, neighbor_weight))

        total_weight = sum(abs(weight) for term, weight in expanded)
        if total_weight == 0:
            return []
        else:
            return [(uri_prefix(term), weight / total_weight) for (term, weight) in expanded]

    def expanded_vector(self, terms, limit_per_term=10, include_neighbors=True):
        self.load()
        return weighted_average(
            self.frame,
            self.expand_terms(terms, limit_per_term, include_neighbors)
        )

    def text_to_vector(self, language, text):
        tokens = wordfreq.tokenize(text, language)
        weighted_terms = [(standardized_uri(language, token), 1.) for token in tokens]
        return self.get_vector(weighted_terms, include_neighbors=False)

    def get_vector(self, query, include_neighbors=True):
        """
        Given one of the possible types of queries (see `similar_terms`), make
        a vector to look up from it.

        If there are 5 or fewer terms involved and `include_neighbors=True`, this
        will allow expanded_vector to look up neighboring terms in ConceptNet.
        """
        self.load()
        if isinstance(query, pd.DataFrame) or isinstance(query, dict):
            terms = list(query.items())
        elif isinstance(query, str):
            terms = [(query, 1.)]
        elif isinstance(query, list):
            terms = query
        else:
            raise ValueError("Can't make a query out of type %s" % type(query))
        include_neighbors = include_neighbors and (len(terms) <= 5)
        vec = self.expanded_vector(terms, include_neighbors=include_neighbors)
        return normalize_vec(vec)

    def similar_terms(self, query, filter=None, limit=20):
        """
        Get a DataFrame of terms ranked by their similarity to the query.
        The query can be:

        - A DataFrame of weighted terms
        - A dictionary from terms to weights
        - A list of (term, weight) tuples
        - A single term

        If the query contains 5 or fewer terms, it will be expanded to include
        neighboring terms in ConceptNet.
        """
        self.load()
        vec = self.get_vector(query)
        small_vec = vec[:self.small_k]
        search_frame = self.small_frame
        if filter:
            exact_only = filter.count('/') >= 3
            if filter.endswith('/.'):
                filter = filter[:-2]
                exact_only = True
            if exact_only:
                if filter in search_frame.index:
                    idx = search_frame.index.get_loc(filter)
                    search_frame = search_frame[idx:idx+1]
                else:
                    search_frame = search_frame.iloc[0:0]
            else:
                start_key = filter
                # '0' is the character after '/', so end_key is the first possible
                # key that's not a descendant of the given filter key
                end_key = filter + '0'
                try:
                    start_idx = search_frame.index.get_loc(start_key, method='bfill')
                except KeyError:
                    start_idx = len(search_frame.index)
                try:
                    end_idx = search_frame.index.get_loc(end_key, method='bfill')
                except KeyError:
                    end_idx = len(search_frame.index)
                search_frame = search_frame.iloc[start_idx:end_idx]
        similar_sloppy = similar_to_vec(search_frame, small_vec, limit=limit * 50)
        similar_choices = l2_normalize_rows(self.frame.loc[similar_sloppy.index].astype('f'))

        similar = similar_to_vec(similar_choices, vec, limit=limit)
        return similar

    def get_similarity(self, query1, query2):
        vec1 = self.get_vector(query1)
        vec2 = self.get_vector(query2)
        return cosine_similarity(vec1, vec2)
