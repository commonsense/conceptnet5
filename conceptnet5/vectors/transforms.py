import pandas as pd
import numpy as np
from conceptnet5.nodes import standardized_concept_uri


def standardize_row_labels(frame, language='en'):
    """
    Convert a frame whose row labels are bare English terms to one whose row
    labels are standardized ConceptNet URIs. Rows whose labels get the same
    standardized URI get combined, with earlier rows given more weight.
    """
    frame.index = pd.Series(
        [standardized_concept_uri(language, label) for label in frame.index],
        name='term'
    )
    nrows = frame.shape[0]
    weights = 1.0 / np.arange(1, nrows + 1)
    label_weights = pd.Series(weights, index=frame.index)

    relabeled = frame.mul(weights, axis='rows').sort_index().groupby(level=0).sum()
    combined_weights = label_weights.sort_index().groupby(level=0).sum()
    return relabeled.div(combined_weights, axis='rows')

