
import threading, Queue, subprocess
import re, sys, os
import marshal, struct
from conceptnet5.edges import make_edge, MultiWriter



NUMBER_OF_WORKERS = 5


#this will read a single file by breaking it into chunks
#it then delegates the processing of these chunks to 
#SubprocessManagerWorkers.  These SubprocessManagers fork their own 
#subprocesses, pull chunks out of a queue and  hand over the 
# chunks to the subprocess to quickly handle.   
class MultiReader():
	def __init__(self,file_name,multiwriter_filename,reader_file_path):
		self.multiwriter_filename = multiwriter_filename
		self.file_name = file_name
		self.reader_file_path = reader_file_path
		self.queue = Queue.Queue()

		self.start_workers()
		self.fill_queue()
		
		self.queue.join()
		print "finished"

	def start_workers(self):
		#fire up a bunch of workers (typically one per core)
	    for i in range(NUMBER_OF_WORKERS):
	        print "worker started"
	        w = SubprocessManagerWorker(self.queue,self.reader_file_path)
	        w.setDaemon(1)
	        w.start()

	def fill_queue(self):
		chunksize = max(1, os.path.getsize(self.file_name) / NUMBER_OF_WORKERS / (1024*1024))

		chunk_number = 0
		# distribute the chunks
		for chunk in self.getchunks(self.file_name, chunksize*1024*1024):
			chunk_start = chunk[0]
			chunk_size = chunk[1]
			self.queue.put((self.file_name, chunk_start,chunk_size,chunk_number,self.multiwriter_filename))
			chunk_number += 1
	def getchunks(self,file, size=1024*1024):
	    # yield sequence of (start, size) chunk descriptors
		f = open(file, "r")
		while 1:
			start = f.tell()
			f.seek(size, 1)
			s = f.readline() # skip forward to next line ending
			yield start, f.tell() - start
			if not s:
				break


#This class starts a single subprocess which it hands chunks to
#one by one to process.
class SubprocessManagerWorker(threading.Thread):

    def __init__(self,queue,reader_file_path):
        threading.Thread.__init__(self)

        python_executable = [sys.executable]
        
        #this is calling:
        # python read_x_.py --subprocess
        #this method must be calling something from within
        #reader_x_.py because that has the appropriate handle_lines method
        self.process = subprocess.Popen(
            python_executable + [reader_file_path] + ["--subprocess"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
            )

        self.stdin = self.process.stdin
        self.stdout = self.process.stdout
        self.queue = queue

    def run(self):
        while 1:
        	#grabs a command with instructions on what chunk to process
        	#and where to write the output.
            cmd = self.queue.get()
            self.start_subprocess_to_handle_chunk(self.stdin, cmd)

            #hangs til subprocess finishes with chunk
            self.get_finished_signal_from_subprocess(self.stdout)
            self.queue.task_done()

    def start_subprocess_to_handle_chunk(self,file, object):
        data = marshal.dumps(object)
        self.stdin.write(struct.pack("I", len(data)))
        self.stdin.write(data)
        self.stdin.flush()

    def get_finished_signal_from_subprocess(self,stdout):
        try:
            n = struct.unpack("I", stdout.read(4))[0]
        except struct.error:
            return None
        return marshal.loads(stdout.read(n))

#this class is what is run by the subprocess,
#it is delegated chunks to handle by a subprocessManagerWorker
#there is one of these for each subprocessManagerWorker
class FileChunkProcessor(object):
	def __init__(self,handle_lines):
		#this is the method used to create edges from the lines
		#and write the edges to the flat and solr json files
		self.handle_lines = handle_lines

		self.start()

	def start(self):
		while 1:
			#get arguments from the pipe
			args = self.getobject(sys.stdin)

			#if there are no arguments, we are done
			if args is None:
				sys.exit(0)

			#unpack arguments
			file_name = args[0]
			chunk_start= args[1]
			chunk_size = args[2]
			chunk_number = args[3]
			multi_writer_filename = args[4]

			#process the chunk given by the args
			self.processChunk(file_name,chunk_start,chunk_size,chunk_number,multi_writer_filename)

			#let the multireader know we have finished our chunk
			#and are ready for another one
			self.putobject(sys.stdout, "finished with chunk")

	def processChunk(self,file_name,chunk_start,chunk_size,chunk_number,multi_writer_filename):
		my_file = open(file_name)

		writer = MultiWriter(str(multi_writer_filename) + "_"+ str(chunk_number))
		my_file.seek(chunk_start)
		lines = my_file.readlines(chunk_size)

		self.handle_lines(lines,writer)


	def putobject(self,file, object):
		data = marshal.dumps(object)
		file.write(struct.pack("I", len(data)))
		file.write(data)
		file.flush()

	def getobject(self,file):
	    try:
	        n = struct.unpack("I", file.read(4))[0]
	    except struct.error:
	        return None
	    return marshal.loads(file.read(n))






