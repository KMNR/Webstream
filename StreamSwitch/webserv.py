import settings,utilities

def writestatus(self):
	pid = utilities.getstatus()
	if pid:
		self.wfile.write("on")
	else:
		self.wfile.write("off")



def bgserver(name):
	import string,cgi,time,os,sys,threading,re
	from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
	from SocketServer import ThreadingMixIn
	
	class MyHandler(BaseHTTPRequestHandler):
		passex = re.compile('password=(.*)')
		def do_POST(self):
			self.send_response(200)
			self.send_header('Content-type','text/html')
			self.end_headers()
			length = int(self.headers.getheader('content-length'))
			stuff = self.rfile.read(length)
			passwd = None
			if self.passex.match(stuff):
				passwd = self.passex.match(stuff).group(1)
			if passwd == settings.password:

				if self.path == "/api/on":
					os.system("sudo /etc/init.d/darkice start")
					writestatus(self)
				elif self.path == "/api/off":
					os.system("sudo /etc/init.d/darkice stop")
					writestatus(self)
			else:
				self.wfile.write("go away")

		def do_GET(self):
			self.send_response(200)
			self.send_header('Content-type','text/html')
			self.end_headers()

			if self.path == "/api/on":
				writestatus(self)
			elif self.path == "/api/off":
				writestatus(self)
			elif self.path == "/api/status":
				writestatus(self)
			else:
				self.wfile.write("<html><head title='KAWCS'></head><body><h1>Kmnr Advanced Webstream Control System</h1>")
				self.wfile.write("<br><div>type password here to turn on:<form action='/api/on' method='POST'><input type='password' name='password'><submit></form></div>")
				self.wfile.write("<br><div>type password here to turn off:<form action='/api/off' method='POST'><input type='password' name='password'><submit></form></div>")
				self.wfile.write("<hr>The webstream is currently <span class='")
				writestatus(self)
				self.wfile.write("'>")
				writestatus(self)
				self.wfile.write("</span>")
				self.wfile.write("</body></html>")


	class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
		pass
	
	server = ThreadedHTTPServer((settings.host,settings.port), MyHandler)
	print "started webserver on port " + str(settings.port)
	server.serve_forever()


