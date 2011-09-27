from neo4jrestclient.client import GraphDatabase, Index, Node
from conceptnet5.assertion import get_assertion

def justifies(assertion1, assertion2, weight=1.0):
    """
    Takes two existing assertions, `assertion1` and `assertion2`, and
    records the fact that `assertion1` justifies `assertion2`. An optional
    weight between -1 and 1 may be given.
    """
    assertion1.relationships.create('justifies', assertion2, weight=weight)
