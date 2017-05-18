from conceptnet5.vectors.formats import load_hdf, save_hdf
import numpy as np
import pandas as pd


def get_concept_degrees(filename):
    concept_degrees = {}
    with open(filename) as infile:
        for line in infile:
            line = line.strip()
            if line:
                numstr, uri = line.split(' ', 1)
                count = int(numstr)
                if count == 1:
                    break
                concept_degrees[uri] = count
    return concept_degrees


def compute_tsne(input_filename, degree_filename, output_filename):
    from tsne import bh_sne
    concept_degrees = get_concept_degrees(degree_filename)
    frame = load_hdf(input_filename)

    # Exclude Chinese because, so far, its vectors aren't alignable with
    # other languages
    vocab = [
        term for term in frame.index
        if concept_degrees.get(term, 0) >= 10
        and not term.startswith('/c/zh/')
    ]
    v_frame = frame.loc[vocab].astype(np.float64)
    tsne_coords = bh_sne(v_frame.values, perplexity=50.)
    tsne_frame = pd.DataFrame(tsne_coords, index=v_frame.index)
    save_hdf(tsne_frame, output_filename)
