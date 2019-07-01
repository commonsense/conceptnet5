import marisa_trie
import numpy as np
import pandas as pd

import wordfreq
from conceptnet5.db.query import AssertionFinder
from conceptnet5.uri import get_uri_language, split_uri, uri_prefix
from conceptnet5.util import get_data_filename
from conceptnet5.vectors import (
    cosine_similarity,
    normalize_vec,
    similar_to_vec,
    standardized_uri,
    weighted_average,
)
from conceptnet5.vectors.formats import load_hdf
from conceptnet5.vectors.transforms import l2_normalize_rows

# Magnitudes smaller than this tell us that we didn't find anything meaningful
SMALL = 1e-6


class MissingVectorSpace(Exception):
    pass


def field_match(value, query):
    """
    Determines whether a given field of an edge (or, in particular, an
    assertion) matches the given query.

    If the query is a URI, it will match prefixes of longer URIs, unless `/.` is
    added to the end of the query.

    For example, `/c/en/dog` will match assertions about `/c/en/dog/n/animal`,
    but `/c/en/dog/.` will only match assertions about `/c/en/dog`.
    """
    query = query.rstrip('/')
    if isinstance(value, list):
        return any(field_match(subval, query) for subval in value)
    elif query.endswith('/.'):
        return value == query[:-2]
    else:
        return value[: len(query)] == query and (
            len(value) == len(query) or value[len(query)] == '/'
        )


class VectorSpaceWrapper(object):
    """
    An object that wraps the data necessary to look up vectors for terms
    (in the vector space named Conceptnet Numberbatch) and find related terms.

    The filenames usually don't need to be specified, because the system will
    look in default locations for them. They can be specified to replace them
    with toy versions for testing, or to evaluate how other embeddings perform
    while still using ConceptNet for looking up words outside their vocabulary.
    """

    def __init__(self, vector_filename=None, frame=None, use_db=True):
        if frame is None:
            self.frame = None
            self.vector_filename = vector_filename or get_data_filename(
                'vectors/mini.h5'
            )
        else:
            self.frame = frame
            self.vector_filename = None
        self.small_frame = None
        self.k = None
        self.small_k = None
        self.finder = None
        self.trie = None
        self.cache = {}
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

            if not self.frame.index[1].startswith('/c/'):
                # These terms weren't in ConceptNet standard form. Assume
                # they're in English, and stick the English language tag on
                # them without any further transformation, so we can be sure
                # we're evaluating the vectors as provided.
                self.finder = None
                self.frame.index = ['/c/en/' + label for label in self.frame.index]

            if not self.frame.index.is_monotonic_increasing:
                self.frame = self.frame.sort_index()

            self.k = self.frame.shape[1]
            self.small_k = 100
            self.small_frame = self.frame.iloc[:, : self.small_k].copy()
        except OSError:
            raise MissingVectorSpace(
                "Couldn't load the vector space %r. Do you need to build or "
                "download it?" % self.vector_filename
            )
        self._build_trie()

    def _build_trie(self):
        """
        Build a trie (a prefix tree) that allows finding terms by their
        prefixes.
        """
        self._trie = marisa_trie.Trie(list(self.frame.index))

    @staticmethod
    def passes_filter(label, filter):
        if filter is None:
            return True
        else:
            return field_match(label, filter)

    @staticmethod
    def _englishify(term):
        splits = split_uri(term)
        if len(splits) > 2:
            englishified = '/c/en/' + splits[2]
            return englishified

    def _find_neighbors(self, term, limit_per_term, weight):
        neighbors = []
        for edge in self.finder.lookup(term, limit=limit_per_term):
            if field_match(edge['start']['term'], term) and not field_match(
                edge['end']['term'], term
            ):
                neighbor = edge['end']['term']
            elif field_match(edge['end']['term'], term) and not field_match(
                edge['start']['term'], term
            ):
                neighbor = edge['start']['term']
            else:
                continue
            neighbor_weight = weight * min(10, edge['weight']) * 0.01
            neighbors.append((neighbor, neighbor_weight))
        return neighbors

    def _match_prefix(self, term, prefix_weight):
        results = []
        while term:
            # Skip excessively general lookups, for either an entire
            # language, or all terms starting with a single
            # non-ideographic letter
            if (
                len(split_uri(term)) < 3
                or term.endswith('/')
                or (term[-2] == '/' and term[-1] < chr(0x3000))
            ):
                break
            prefixed = self._terms_with_prefix(term)
            if prefixed:
                n_prefixed = len(prefixed)
                for prefixed_term in prefixed:
                    results.append((prefixed_term, prefix_weight / n_prefixed))
                break
            term = term[:-1]
        return results

    def expand_terms(self, terms, limit_per_term=10, oov_vector=True):
        """
        Given a list of weighted terms as (term, weight) tuples, add terms that
        are one step away in ConceptNet at a lower weight, terms in English that share the
        surface form with these terms, and the terms which share prefix with these terms,
        if the terms are OOV.

        This helps increase the recall power of the vector space, because it
        means you can find terms that are too infrequent to have their own
        vector by looking up their neighbors, etc.

        This forms a reasonable approximation of the vector an infrequent term would have anyway.
        """
        self.load()
        expanded = terms[:]
        for term, weight in terms:
            if oov_vector and term not in self.frame.index and self.finder is not None:
                neighbors = self._find_neighbors(term, limit_per_term, weight)
                expanded.extend(neighbors)

                prefix_weight = 0.01
                if get_uri_language(term) != 'en':
                    englishified = self._englishify(term)
                    expanded.append((englishified, prefix_weight))

                prefix_matches = self._match_prefix(term, prefix_weight)
                expanded.extend(prefix_matches)

        total_weight = sum(abs(weight) for term, weight in expanded)
        if total_weight == 0:
            return []
        else:
            return [
                (uri_prefix(term), weight / total_weight) for (term, weight) in expanded
            ]

    def expanded_vector(self, terms, limit_per_term=10, oov_vector=True):
        """
        Given a list of weighted terms as (term, weight) tuples, make a vector
        representing information from:

        - The vectors for these terms
        - The vectors for their neighbors in ConceptNet
        - The vectors for terms that share a sufficiently-long prefix with
          any terms in this list that are out-of-vocabulary
        """
        self.load()
        return weighted_average(
            self.frame, self.expand_terms(terms, limit_per_term, oov_vector)
        )

    def text_to_vector(self, language, text):
        """
        Used in Story Cloze Test to create a vector for text.
        """
        tokens = wordfreq.tokenize(text, language)
        weighted_terms = [
            (uri_prefix(standardized_uri(language, token)), 1.) for token in tokens
        ]
        return self.get_vector(weighted_terms, oov_vector=False)

    def get_vector(self, query, oov_vector=True):
        """
        Given one of the possible types of queries (see `similar_terms`), make
        a vector to look up from it.

        If there are 5 or fewer terms involved and `oov_vector=True`, this
        will allow expanded_vector to look up neighboring terms in ConceptNet.
        """
        self.load()

        if isinstance(query, np.ndarray):
            return query
        elif isinstance(query, pd.Series) or isinstance(query, dict):
            terms = list(query.items())
        elif isinstance(query, pd.DataFrame):
            terms = list(query.to_records())
        elif isinstance(query, str):
            terms = [(query, 1.)]
        elif isinstance(query, list):
            terms = query
        else:
            raise ValueError("Can't make a query out of type %s" % type(query))

        cache_key = tuple(terms + [oov_vector])
        if cache_key in self.cache:
            return self.cache[cache_key]

        oov_vector = oov_vector and (len(terms) <= 5)

        vec = self.expanded_vector(terms, oov_vector=oov_vector)
        self.cache[cache_key] = normalize_vec(vec)
        return self.cache[cache_key]

    def similar_terms(self, query, filter=None, limit=20):
        """
        Get a Series of terms ranked by their similarity to the query.
        The query can be:

        - A pandas Series of weighted terms
        - A pandas DataFrame of weighted terms
        - A dictionary from terms to weights
        - A list of (term, weight) tuples
        - A single term
        - An existing vector

        If the query contains 5 or fewer terms, it will be expanded to include
        neighboring terms in ConceptNet.
        """
        self.load()
        vec = self.get_vector(query)
        small_vec = vec[: self.small_k]
        search_frame = self.small_frame
        # TODO: document filter
        if filter:
            exact_only = filter.count('/') >= 3
            if filter.endswith('/.'):
                filter = filter[:-2]
                exact_only = True
            if exact_only:
                if filter in search_frame.index:
                    idx = search_frame.index.get_loc(filter)
                    search_frame = search_frame[idx : idx + 1]
                else:
                    search_frame = search_frame.iloc[0:0]
            else:
                start_idx, end_idx = self._index_prefix_range(filter + '/')
                search_frame = search_frame.iloc[start_idx:end_idx]
        similar_sloppy = similar_to_vec(search_frame, small_vec, limit=limit * 50)
        similar_choices = l2_normalize_rows(
            self.frame.loc[similar_sloppy.index].astype('f')
        )

        similar = similar_to_vec(similar_choices, vec, limit=limit)
        return similar

    def get_similarity(self, query1, query2):
        vec1 = self.get_vector(query1)
        vec2 = self.get_vector(query2)
        return cosine_similarity(vec1, vec2)

    def _terms_with_prefix(self, prefix):
        """
        Get a list of terms whose URI begins with the given prefix. The list
        will be in an arbitrary order.
        """
        return self._trie.keys(prefix)

    def _index_prefix_range(self, prefix):
        """
        Get the range of indices on the DataFrame we're wrapping that begin
        with a given prefix.

        The range is a pair of index numbers. Following the convention of
        Python ranges, the starting index is inclusive, while the end index
        is exclusive.

        Returns the empty range (0, 0) if no terms begin with this prefix.
        """
        # Use the trie to find all terms with the given prefix. Then sort them,
        # because the range will span from our first prefix in sorted
        # order to just after our last.
        terms = sorted(self._terms_with_prefix(prefix))
        if not terms:
            return (0, 0)

        start_loc = self.frame.index.get_loc(terms[0])
        end_loc = self.frame.index.get_loc(terms[-1]) + 1
        return start_loc, end_loc
