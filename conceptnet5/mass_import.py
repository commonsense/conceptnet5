from conceptnet5.graph import get_graph
from conceptnet5.whereami import get_project_filename
import codecs
import sys, traceback
import time
from neo4jrestclient.request import StatusException

def run_in_db(graph, command, tries=5):
    for i in xrange(tries):
        try:
            sys.stdout.write('.')
            sys.stdout.flush()
            return graph.gremlin_query(command)
        except StatusException, e:
            if '500' in str(e):
                print '?'
                time.sleep(0.5)
            else:
                raise

def batch_import(filename):
    graph = get_graph()
    
    # Make sure the DB has the appropriate global functions loaded.
    with open(get_project_filename('gremlin/setup.gremlin')) as setup_file:
        graph.gremlin_query(setup_file.read())

    with open(filename) as data_file:
        queue = []
        for line in data_file:
            queue.append(line.decode('utf-8'))
            if len(queue) >= 50:
                run_in_db(graph, u''.join(queue))
                queue = []
        run_in_db(graph, u''.join(queue))

if __name__ == '__main__':
    import sys
    batch_import(sys.argv[-1])
