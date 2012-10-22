import sys
from conceptnet5.edges import make_edge, MultiWriter
import marshal, struct

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
			multi_writer_filename = args[3]

			#process the chunk given by the args
			self.processChunk(file_name,chunk_start,chunk_size,multi_writer_filename)

			#let the multireader know we have finished our chunk
			#and are ready for another one
			self.putobject(sys.stdout, "finished with chunk")

	def processChunk(self,file_name,chunk_start,chunk_size,multi_writer_filename):
		my_file = open(file_name)

		writer = MultiWriter(str(multi_writer_filename) + str(chunk_start)+ '.txt')
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



