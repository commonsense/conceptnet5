from neo4jrestclient.client import GraphDatabase, Index, Node

def fuzzy_logic_scale(score):
    if score < 0.:
        return 0.
    return score / (1.0+score)

def parallel(a, b):
    """
    Returns a value that scales with `a` and `b` and is less than both, as
    if they were resistances in parallel. Used for evaluating conjunctions.

    Negative confidence makes no sense here, so it just bottoms out at 0.
    One completely unreliable node in a conjunction makes the whole conjunction
    completely unreliable.

    On the `fuzzy_logic_scale`, this becomes the Hamacher product:
        
        a*b / (a + b - a*b)
    """
    if a <= 0. or b <= 0.:
        return 0.
    return float(a*b) / (a + b)

