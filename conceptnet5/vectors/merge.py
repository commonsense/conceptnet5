import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize

from conceptnet5.languages import CORE_LANGUAGES
from conceptnet5.uri import get_uri_language

from .formats import load_hdf


def dataframe_svd_projection(frame, k):
    """
    Factor a dataframe into two matrices with `k` columns, using the labels
    from the dataframe as the row labels.

    The matrices that are returned are `uframe` and `vframe`. `uframe` assigns
    a k-dimensional vector to each row of the frame, and `vframe` assigns a
    k-dimensional vector to each column. One way to think of these is that
    `uframe` contains the rows of `frame` projected into a k-dimensional space,
    while `vframe` is the operation that projects those rows.
    """
    U, Σ, Vt = np.linalg.svd(frame.values, full_matrices=False)
    uframe = pd.DataFrame(U[:, :k], index=frame.index, dtype='f')
    vframe = pd.DataFrame(Vt.T[:, :k], index=frame.columns, dtype='f')
    return uframe, Σ[:k], vframe


def concat_intersect(frame_filenames):
    """
    Find the intersection of the labels of all the frames in the given
    files , and concatenate the vectors that the frames have for each of
    those labels.

    This is exactly what `pd.concat` is for. However, `pd.concat` uses too
    much memory. We have to emulate what it does while building the result
    within a single matrix, instead of having multiple intermediate matrices.
    """
    # Each frame will be associated with a range of columns in our concatenated
    # frame. As we scan through the frames, find out what the indices of those
    # columns are.
    frame_col_offsets = [0]
    assert len(frame_filenames) > 0
    frame = load_hdf(frame_filenames[0])
    ncolumns = frame.shape[1]

    # Our label intersection starts out as the label set of the first frame.
    label_intersection = set(frame.index)

    # Narrow down the label intersection, and find the column offset of
    # each subsequent frame.
    for frame_filename in frame_filenames[1:]:
        frame = load_hdf(frame_filename)
        label_intersection &= set(frame.index)
        frame_col_offsets.append(ncolumns)
        ncolumns += frame.shape[1]

    # Get the list of labels in a predictable order.
    label_intersection = sorted(label for label in label_intersection)
    nrows = len(label_intersection)

    # Now we know how many rows and columns of data we have, so allocate the
    # NumPy array that will contain our results.
    joindata = np.zeros((nrows, ncolumns), 'f')

    # Find the appropriate rows of each frame, extract them in the order of
    # our labels, and set those as the appropriate columns of the merged array.
    for frame_filename, offset in zip(frame_filenames, frame_col_offsets):
        frame = load_hdf(frame_filename)
        width = frame.shape[1]
        for i, label in enumerate(label_intersection):
            joindata[i, offset : (offset + width)] = frame.loc[label].values
    del frame

    # Convert the array to a DataFrame with the appropriate labels, and
    # return it.
    joined = pd.DataFrame(joindata, index=label_intersection)
    return joined


def merge_intersect(frame_filenames, subsample=20, k=300):
    """
    Combine the vector knowledge contained in the frames over the vocabulary
    that they agree on, and use dimensionality reduction to mitigate the
    redundancy of learning the same thing multiple ways.

    If their vocabularies result from retrofitting, then the resulting
    vocabulary will be the vocabulary of the retrofit knowledge graph,
    plus any other terms that happen to be in all of the frames.
    """
    # Find the intersected vocabulary of the frames, and concatenate their
    # vectors over that vocabulary.
    joined = concat_intersect(frame_filenames)

    # Find a subset of the labels that we'll use for calculating the
    # dimensionality-reduced version. The labels we particularly care about
    # are single words in our CORE_LANGUAGES. Even those are too numerous,
    # so we take an arbitrary 1/n sample of them, where n is given by the
    # `subsample` parameter.
    filtered_labels = pd.Series(
        [
            label
            for (i, label) in enumerate(joined.index)
            if i % subsample == 0
            and '_' not in label
            and get_uri_language(label) in CORE_LANGUAGES
        ]
    )

    # Mean-center and L_2-normalize the data, to prevent artifacts
    # in dimensionality reduction.
    adjusted = joined.loc[filtered_labels]
    adjusted -= joined.mean(0)
    normalize(adjusted.values, norm='l2', copy=False)

    # The SVD of this normalized matrix will give us its projection into
    # a lower-dimensional space (`projected`), as well as the operator that
    # performs that projection (`projection`) and the relative weights of the
    # columns (`eigenvalues`).
    projected, eigenvalues, projection = dataframe_svd_projection(adjusted, k)

    # We don't actually need this smaller matrix or its projection anymore;
    # what we learned is how to project _any_ matrix into this space.
    del adjusted
    del projected

    # Project the original `joined` matrix into this space using the
    # `projection` operator.
    reprojected = joined.dot(projection)
    del joined

    # `projection` (V) is an orthogonal matrix, so when we multiply by it, we
    # get a `reprojected` that approximately preserves distances (U * Σ).
    #
    # But these distances reflect redundant features among the input matrices.
    # To mitigate this redundancy, and to match Levy and Goldberg's observation
    # that U * Σ ** (1/2) is a better SVD projection for word-representation
    # purposes than U * Σ, we divide by Σ ** (1/2).
    np.divide(reprojected.values, eigenvalues ** .5, out=reprojected.values)
    normalize(reprojected.values, norm='l2', copy=False)

    # Return our unified vectors, and the projection that could map other
    # concatenated vectors into the same vector space.
    return reprojected, projection
