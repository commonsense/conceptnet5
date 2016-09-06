from conceptnet5.util import get_support_data_filename
from conceptnet5.vectors import standardized_uri, get_vector, similar_to_vec
from conceptnet5.vectors.query import VectorSpaceWrapper
import wordfreq


def read_google_analogies(filename):
    quads = [
        [standardized_uri('en', term) for term in line.rstrip().split(' ')]
        for line in open(filename, encoding='utf-8')
        if not line.startswith(':')
    ]
    return quads


def analogy_func(frame, a1, b1, a2):
    return get_vector(frame, b1) - get_vector(frame, a1) + get_vector(frame, a2)


def eval_analogies(frame):
    filename = get_support_data_filename('google-analogies/questions-words.txt')
    quads = read_google_analogies(filename)
    vocab = [
        standardized_uri('en', word)
        for word in wordfreq.top_n_list('en', 100000)
    ]
    tframe = frame.loc[vocab]
    total = 0
    correct = 0
    for quad in quads:
        if all(term in tframe.index for term in quad):
            prompt = quad[:3]
            answer = quad[3]
            vector = analogy_func(frame, *prompt)
            similar = similar_to_vec(tframe, vector)
            result = None
            for match in similar.index:
                if match not in prompt:
                    result = match
                    break
            if result == answer:
                correct += 1
            else:
                print(
                    "%s : %s :: %s : %s (should be %s)"
                    % (quad[0], quad[1], quad[2], result.upper(), answer)
                    )
            total += 1
    return correct, total, correct / total
