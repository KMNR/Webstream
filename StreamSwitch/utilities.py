def getstatus():
	import os
	f = os.popen("/etc/init.d/darkice status")
	try:
		pid = f.readlines()[0].rstrip('\n')
	except:
		pid = 0
	return pid
