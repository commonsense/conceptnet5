"""
Given a node, delete all nodes not related to it.
"""

__author__ = 'Justin Venezuela (jven@mit.edu)'

import graph

def get_conceptnet_graph():
  conceptnet_uri = 'http://new-caledonia.media.mit.edu:7474/db/data'
  conceptnet_graph = graph.ConceptNetGraph(conceptnet_uri)
  return conceptnet_graph

def get_root_node(conceptnet_graph):
  root_uri = '/'
  root = conceptnet_graph.get_node(root_uri)
  return root

def traverse(root):
  pass

def mark_nodes(root):
  traversal = root.traverse()
  # print len(traversal)
  for node in traversal:
    pass
    #node.set('__is_connected_to_root', True)

def delete_unmarked_nodes():
  # TODO(jven): how do i iterate over all nodes?
  pass

def unmark_marked_nodes(root):
  pass

def main():
  conceptnet_graph = get_conceptnet_graph()
  root = get_root_node(conceptnet_graph)
  mark_nodes(root)
  delete_unmarked_nodes()
  unmark_marked_nodes()

if __name__ == '__main__':
  main()
