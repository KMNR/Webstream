#!/usr/bin/python

import thread,time
from webserv import bgserver
thread.start_new_thread(bgserver,("web",))

while True:
	time.sleep(10)
