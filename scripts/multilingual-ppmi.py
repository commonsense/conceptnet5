import pandas as pd
from ordered_set import OrderedSet
import argparse
import pathlib
import random
from conceptnet5.vectors.formats import save_hdf
from conceptnet5.vectors.transforms import l2_normalize_rows
from conceptnet5.vectors.ppmi import counts_to_ppmi
from conceptnet5.vectors import replace_numbers
from conceptnet5.nodes import standardized_concept_uri
from wordfreq import get_frequency_dict
from scipy import sparse
from scipy.sparse import linalg


def sparse_from_parallel_text(input_path, languages):
    vocabs = {language: set(get_frequency_dict(language)) for language in languages}
    labels = OrderedSet()
    pairs = OrderedSet()
    rows = []
    cols = []
    values = []

    for lang1 in languages:
        for lang2 in languages:
            if lang1 < lang2:
                print(lang1, lang2)
                filename = input_path / "{}-{}.txt".format(lang1, lang2)
                with open(str(filename), encoding='utf-8') as infile:
                    lines = list(infile.readlines())
                    random.shuffle(lines)
                    for i, line in enumerate(lines):
                        text1, text2 = line.rstrip('\n').split('\t')
                        terms1 = [replace_numbers(standardized_concept_uri(lang1, word)) for word in text1.split(' ') if word in vocabs[lang1]]
                        terms2 = [replace_numbers(standardized_concept_uri(lang2, word)) for word in text2.split(' ') if word in vocabs[lang2]]
                        terms = terms1 + terms2
                        if i > 0 and i % 100000 == 0:
                            print('\t', i, '\t', len(values), terms)
                        if i == 1000000:
                            break
                        for t1 in terms:
                            index1 = labels.add(t1)
                            for t2 in terms:
                                index2 = labels.add(t2)
                                pair_index = pairs.add((index1, index2))
                                assert pair_index <= len(values)
                                if pair_index == len(values):
                                    rows.append(index1)
                                    cols.append(index2)
                                    values.append(1 / len(terms))
                                else:
                                    values[pair_index] += 1 / len(terms)

    shape = (len(labels), len(labels))
    index = pd.Index(labels)
    mat = sparse.coo_matrix(
        (values, (rows, cols)),
        shape=shape, dtype='f'
    ).tocsr()

    return mat, index


def build_ppmi(input_path, output_path):
    spmat, index = sparse_from_parallel_text(
        pathlib.Path(input_path),
        ['de', 'en', 'es', 'fa', 'it']
    )
    ppmi = counts_to_ppmi(spmat)
    u, s, vT = linalg.svds(ppmi, 300)
    v = vT.T
    values = (u + v) * (s ** 0.5)
    ppmi_frame = l2_normalize_rows(pd.DataFrame(values, index=index))
    save_hdf(ppmi_frame, output_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='directory of parallel text')
    parser.add_argument(
        '-o', '--output', help='msgpack file to output to'
    )
    args = parser.parse_args()
    build_ppmi(args.input, args.output)


if __name__ == '__main__':
    main()
