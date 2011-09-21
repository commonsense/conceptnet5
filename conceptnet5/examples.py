"""
Here are some examples of nodes and edges one could work with...
"""
from neo4jrestclient.client import GraphDatabase, Index
g = GraphDatabase("http://new-caledonia.media.mit.edu:7474/db/data/")

otter = g.node(name='otter', language='en', type='concept')
fur = g.node(name='fur', language='en', type='concept')
has = g.node(name='Has', type='relation')

print otter.properties

assertion = g.node(type='assertion')

assertion.relationships.create("relation", has)
assertion.relationships.create("arg", otter, position=1)
assertion.relationships.create("arg", fur, position=2)

print assertion.id
