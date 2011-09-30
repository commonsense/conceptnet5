# -*- coding: utf-8 -*-

from conceptnet5.graph import *
def test_create_assertions_twice():
    g = ConceptNetGraph('http://localhost:7474/db/data')
    a1 = g.get_or_create_node(u"/assertion/_/relation/IsA/_/concept/en/dog/_/concept/en/animal")
    assert a1 == g.get_or_create_node(u"/assertion/_/relation/IsA/_/concept/en/dog/_/concept/en/animal")

    a2 = g.get_or_create_node(u"/assertion/_/relation/UsedFor/_/concept/zh_TW/枕頭/_/concept/zh_TW/睡覺")
    assert a2 == g.get_or_create_node(u"/assertion/_/relation/UsedFor/_/concept/zh_TW/枕頭/_/concept/zh_TW/睡覺")
    
    a3 = g.get_or_create_node(u"/assertion/_/relation/IsA/_/concept/en/test_:D/_/concept/en/it works")
    assert a3 == g.get_or_create_node(u"/assertion/_/relation/IsA/_/concept/en/test_:D/_/concept/en/it works")

    just1 = g.get_or_create_edge('justify', 0, a1)
    just2 = g.get_or_create_edge('justify', 0, a2)
    assert just1 == g.get_or_create_edge('justify', 0, a1)
    # TODO: clean up
    
