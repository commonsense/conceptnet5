#this class should be able to multi-thread the readers so that it does not take so long:

from threading import Thread
from Queue import Queue
import time

from conceptnet5.nodes import list_to_uri_piece, uri_piece_to_list, make_assertion_uri, normalize_uri, make_concept_uri, concept_to_lemmas
from hashlib import sha1
import json, os
import cStringIO


# class LineWorker(Thread):

# 	def __init__(self,input_lines_queue,output_edges_queue, handle_line_method):
# 		Thread.__init__(self)
# 		self.input_lines_queue = input_lines_queue
# 		self.output_edges_queue = output_edges_queue
# 		self.handle_line = handle_line_method

# 	def run(self):
# 		while True:
# 			line = self.input_lines_queue.get()
# 			edge = self.handle_line(line)
# 			if edge != None:
# 				self.output_edges_queue.put(edge)
# 			self.input_lines_queue.task_done()



# class EdgeWriterWorker(Thread):

# 		def __init__(self,edges_queue, writer):
# 			Thread.__init__(self)
# 			self.edges_queue = edges_queue
# 			self.writer = writer

# 		def run(self):
# 			while True:
# 				edge = self.edges_queue.get()
# 				self.writer.write(edge)
# 				self.edges_queue.task_done()

class Worker(Thread):
	def __init__(self,input_lines,handle_line_method,writer):
		Thread.__init__(self)
		self.input_lines = input_lines
		self.handle_line_method = handle_line_method
		self.writer = writer

	def run(self):
		for line in self.input_lines:
			edge = self.handle_line_method(line)
			if edge != None:
				self.writer.write(edge)




class RawInputLinesProcessor():
	
	def __init__(self, handle_line_method,num_workers=3):
		self.handle_line_method = handle_line_method
		self.num_workers = num_workers

		self.workers = []

	def read(self,input_lines):
		self.start_workers(input_lines)

		self.wait_until_finished()

	def start_workers(self,input_lines):
		start_index = 0
		lines_per_worker = (int) (len(input_lines)/(1.0*self.num_workers))
		end_index = lines_per_worker
		print end_index
		for i in range(self.num_workers):
			print "start: " + str(start_index)
			print "end: " + str(end_index)
			sub_input_lines = input_lines[start_index:end_index]
			writer = MultiWriter("temporary_" + str(i))
			worker = Worker(sub_input_lines,self.handle_line_method,writer)
			self.workers.append(worker)
			worker.start()
			start_index = end_index
			end_index = end_index + lines_per_worker
			print "worker started"

	def wait_until_finished(self):
		for worker in self.workers:
			worker.join()
		print "all lines have been written"










def make_edge(rel, start, end,
              dataset, license, sources, context='/ctx/all',
              surfaceText=None, weight=1.0):
    """
    Take in the information representing an edge (a justified assertion),
    and output that edge in dictionary from.
    """
    features = [
        "%s %s -" % (start, rel),
        "%s - %s" % (start, end),
        "- %s %s" % (rel, end)
    ]
    uri = make_assertion_uri(rel, [start, end], short=True)
    sources.sort()
    edge_unique_data = [uri, context] + sources
    edge_unique = u' '.join(edge_unique_data).encode('utf-8')
    id = '/e/'+sha1(edge_unique).hexdigest()
    obj = {
        'id': id,
        'uri': uri,
        'rel': rel,
        'start': start,
        'end': end,
        'context': context,
        'dataset': dataset,
        'sources': sources,
        'features': features,
        'license': license,
        'weight': weight,
        'surfaceText': surfaceText
    }
    return obj

class FlatEdgeWriter(object):
    """
    This class and its subclasses give you objects you can use to write
    ConceptNet 5 data structures to files. These files can then be imported
    into databases that allow you to search them.

    The default behavior is simply to write the JSON data to a file, one entry
    per line, without any additional indexing information.
    """
    def __init__(self, filename):
        self.filename = filename
        self.open = True
        self.out = open(filename, 'w')
        self.current_write_block = cStringIO.StringIO()
        self.num_writes = 0

    def write_header(self):
        pass

    def write_footer(self):
        pass

    def write(self, edge):
        line = json.dumps(edge)
        self.current_write_block.write(line)
        #self.num_writes += 1
        if self.num_writes > 10000:
        	self.num_writes = 0
        	print >> self.out, self.current_write_block.getvalue()
        	self.current_write_block.close()
        	self.current_write_block = cStringIO.StringIO()

    def close(self):
        self.write_footer()
        self.out.close()
        self.open = False

class SolrEdgeWriter(FlatEdgeWriter):
    """
    Write a JSON dictionary with a repeated 'add' key, once for each edge,
    and a 'commit' key at the end. This is a format that Solr is good at
    importing.
    """
    def write_header(self):
        print >> self.out, '{'

    def write_footer(self):
        print >> self.out, '  "commit": {}'
        print >> self.out, '}'
    
    def write(self, edge):
        edge = dict(edge)
        startLemmas = ' '.join(concept_to_lemmas(edge['start']))
        endLemmas = ' '.join(concept_to_lemmas(edge['end']))
        relLemmas = ' '.join(concept_to_lemmas(edge['rel']))

        edge['startLemmas'] = startLemmas
        edge['endLemmas'] = endLemmas
        if relLemmas:
            edge['relLemmas'] = relLemmas

        if 'surfaceText' in edge and edge['surfaceText'] is None:
            del edge['surfaceText']

        json_struct = json.dumps({'add': {'doc': edge, 'boost': abs(edge['weight'])}}, indent=2)
        self.current_write_block.write(json_struct[2:-2])
        self.current_write_block.write(',\n')
        #self.num_writes +=1
        if self.num_writes > 10000:
        	self.num_writes = 0
        	print >> self.out, self.current_write_block.getvalue()
        	self.current_write_block.close()
        	self.current_write_block = cStringIO.StringIO()

class MultiWriter(object):
    def __init__(self, basename,core=False):
        flat_file_path = 'data/flat/%s.json' % basename
        solr_file_path = 'data/solr/%s.json' % basename

        if core:
            flat_file_path = 'core_data/flat/%s.json' % basename
            solr_file_path = 'core_data/solr/%s.json' % basename

        self.flat_writer = FlatEdgeWriter(flat_file_path)
        self.solr_writer = SolrEdgeWriter(solr_file_path)
        self.writers = [self.flat_writer, self.solr_writer]
        self.open = True
        self.write_header()

    def write_header(self):
        for writer in self.writers:
            writer.write_header()
    
    def write_footer(self):
        # handled by .close()
        pass

    def close(self):
        for writer in self.writers:
            writer.close()
        self.open = False

    def write(self, edge):
        for writer in self.writers:
            writer.write(edge)

    def __del__(self):
        if self.open:
            self.close()

# class RawInputLinesProcessor():
	
# 	def __init__(self, handle_line_method, writer,num_line_workers=3):
# 		self.handle_line_method = handle_line_method
# 		self.writer = writer
# 		self.num_line_workers = num_line_workers

# 		self.in_q = Queue()
# 		self.out_q = Queue()

# 	def read(self,input_lines,close_writer = True):
# 		self.start_edge_builder_workers()
# 		self.start_edge_writer_worker()
# 		self.load_queue(input_lines)
# 		self.wait_until_finished()

# 		if close_writer:
# 			self.writer.close()
# 		print "finished"

# 	def start_edge_builder_workers(self):
# 		for i in range(self.num_line_workers):
# 			lineWorker = LineWorker(self.in_q,self.out_q, self.handle_line_method)
# 			lineWorker.setDaemon(True)
# 			lineWorker.start()
# 			print "line worker started"

# 	def start_edge_writer_worker(self):
# 		edgeWriterWorker = EdgeWriterWorker(self.out_q,self.writer)
# 		edgeWriterWorker.setDaemon(True)
# 		edgeWriterWorker.start()
# 		print "writer started"

# 	def load_queue(self,input_lines):
# 		for line in input_lines:
# 			self.in_q.put(line)

# 	def wait_until_finished(self):
# 		self.in_q.join()
# 		print "all lines have been processed, just need to finish writing"
# 		time.sleep(3)
# 		self.out_q.join()
# 		print "all lines have been written"

