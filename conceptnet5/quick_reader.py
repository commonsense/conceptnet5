from multiprocessing import Process, JoinableQueue
from conceptnet5.edges import MultiWriter, make_edge

class QuickReader():
	def __init__(self, writer_name,handle_raw_assertion,add_lines_to_queue, isTest = False, num_threads = 5):
		self.writer_name = writer_name
		self.num_threads = num_threads
		self.handle_raw_assertion = handle_raw_assertion
		self.add_lines_to_queue = add_lines_to_queue
		self.queue = JoinableQueue()
		self.isTest = isTest

	def start(self):
		print "begin writing " + self.writer_name
		self.create_processes()
		self.add_lines_to_queue(self.queue)
		self.queue.join()
		print "finished writing " + self.writer_name

	def pull_lines(self,q,writer):
	    while 1:
	        raw_assertion = q.get()
	        edges = self.handle_raw_assertion(raw_assertion)
	        for edge in edges:
	            writer.write(edge)
	        q.task_done()

	def create_processes(self):
	    for i in range(self.num_threads):
	        writer = MultiWriter(self.writer_name + "_" + str(i),self.isTest)
	        p = Process(target = self.pull_lines, args = (self.queue, writer))
	        p.daemon=True
	        p.start()

	# #override in subclass
	# def add_lines_to_queue(self,queue):
	# 	raise NotImplementedError()

	# #override in subclass
	# def handle_raw_assertion(self,raw_assertion):
	# 	raise NotImplementedError()
