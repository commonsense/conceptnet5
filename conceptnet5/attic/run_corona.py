from conceptnet5.graph import ConceptNetGraph

if __name__ == '__main__':
    g = ConceptNetGraph('ganymede.csc.media.mit.edu:30000')
    if g.db.queue.count() == 0:
        g.corona_init()
    while True:
        g.corona_downward_step()
