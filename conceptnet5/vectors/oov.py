from collections import defaultdict
from itertools import combinations

import numpy as np
import pandas as pd
from scipy.sparse import dok_matrix, csr_matrix
from scipy.sparse.linalg import svds
from wordfreq import word_frequency

from conceptnet5.nodes import uri_to_label
from conceptnet5.uri import get_language
from conceptnet5.vectors.formats import load_hdf
from conceptnet5.vectors import cosine_similarity


def get_frequent_terms(frame, n):
    frequent_terms = []
    for uri in frame.index:
        if get_language(uri) == 'en' and '_' not in uri:
            word = uri_to_label(uri)
            freq = word_frequency(word, 'en', wordlist='large')
            frequent_terms.append((uri, freq))
    return [term for term, freq in sorted(frequent_terms, key=lambda x: x[1], reverse=True)[
                                   :500000] if '#' not in term and '.' not in term][:n]


def get_smaller_frame(frame, n):
    freq_terms = get_frequent_terms(frame, n)
    smaller_frame = frame.ix[freq_terms]
    return smaller_frame


def get_all_subwords(frame, low, high):
    subwords = defaultdict(list)
    for uri in frame.index:
        if get_language(uri) == 'en' and '_' not in uri:
            word_subwords = get_word_subwords(low, high, uri)
            for subword in word_subwords:
                subwords[subword].append(uri)
    return subwords


def get_word_subwords(low, high, uri):
    word = uri_to_label(uri)
    word = '<' + word + '>'
    subwords = []
    for length in range(low, high + 1):
        for subset in combinations(word, length):
            subset = ''.join(subset)
            if subset in word:
                subwords.append(subset)
    return subwords


def get_vocab(frame_filename, lang):
    frame = load_hdf(frame_filename)
    vocab = [term for term in frame.index if get_language(term) == lang]
    return vocab


def make_indices(subwords, frame):
    subword_to_index = {sub: i for sub, i in zip(subwords.keys(), range(0, 1000000))}
    word_to_index = {word: i for word, i in zip(frame.index, range(0, 1000000))}
    return subword_to_index, word_to_index


def fill_data(matrix, subwords, subword_to_index, word_to_index):
    for subword in subwords:
        words = subwords[subword]
        subword_index = subword_to_index[subword]
        for word in words:
            word_index = word_to_index[word]
            matrix[word_index][subword_index] = 1
    return matrix


def get_subword_vectors(frame_filename, vocab_len, low, high):
    frame = load_hdf(frame_filename)
    smaller_frame = get_smaller_frame(frame, vocab_len)
    subwords = get_all_subwords(smaller_frame, low, high)
    subword_to_index, word_to_index = make_indices(subwords, smaller_frame)

    # fill a matrix with subword information
    matrix = dok_matrix((len(smaller_frame.index), len(subwords)), dtype=np.float32)
    for subword in subwords:
        words = subwords[subword]
        subword_index = subword_to_index[subword]
        for word in words:
            word_index = word_to_index[word]
            matrix[word_index, subword_index] = 1

    # version with sparse matrices
    u, s, vt = svds(matrix, k=300)
    u_sp = csr_matrix(u.T)
    v_sp = csr_matrix(vt.T)
    s_sp = csr_matrix(s)
    step1 = v_sp.multiply(s_sp)
    step2 = step1.dot(u_sp)  # pseudoinverse

    # version with regular matrices
    # matrix = np.zeros((len(smaller_frame.index), len(subwords)))
    # filled_matrix = fill_data(matrix, subwords, subword_to_index, word_to_index)

    # U, Σ, Vt = np.linalg.svd(filled_matrix, full_matrices=False)
    # uframe = U[:,:300]
    # sframe = Σ[:300]
    # vframe = Vt.T[:, :300]
    # step1 = vframe * sframe
    # pinv = step1.dot(uframe.T) #pseudoinverse
    # n = smaller_frame.values
    # final = pinv.dot(n)
    # final_df = pd.DataFrame(final, index=list(subwords))
    #

    # Evaluation
    # similarities = []
    # for term in smaller_frame.index:
    #     word_subwords = get_word_subwords(low, high, term)
    #     vectors = []
    #     for subword in word_subwords:
    #         try:
    #             vector = np.array(final_df.loc[subword])
    #             vectors.append(vector)
    #         except KeyError:
    #             continue
    #     final_vector = np.mean(vectors, axis=0)
    #     similarity = cosine_similarity(final_vector, smaller_frame.loc[term])
    #     similarities.append(similarity)
    # print(np.mean(similarities))
    return step2
