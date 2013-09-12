import sys, time, datetime, subprocess, os
from daemon import Daemon

BUILD_DIRECTORY = os.getcwd()

class DailyBuildDaemon(Daemon):
	def run(self):
		while True:
			self.printDate()
			self.changeToBuildDirectory()
			self.gitPull()
			self.makeAll()
			self.printDate()
			break

			#sleep one day
			#time.sleep(86400)

	def printDate(self):
		print datetime.datetime.now()

	def changeToBuildDirectory(self):
		os.chdir(BUILD_DIRECTORY)

	def gitPull(self):
		print "git pull"
		p = subprocess.Popen(['git','pull'],stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = p.communicate()
		print out
		print err

	def makeAll(self):
		print "make all"
		p = subprocess.Popen(['make','all'],stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = p.communicate()
		print out
		print err
			


if __name__ == "__main__":
	daemon = DailyBuildDaemon('/tmp/daemon-example.pid',stdout='/di/python/conceptnet5/cnet5_index_builder/cnet5-data/python_daemon_out.txt',stderr='/di/python/conceptnet5/cnet5_index_builder/cnet5-data/python_daemon_out.txt')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		else:
			print "Unknown command"
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart" % sys.argv[0]
		sys.exit(2)