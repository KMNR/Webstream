import time
from datetime import datetime,timedelta
from string import Template
import subprocess
import urllib
import urllib2
import json
import os

from celery.task import task

import util
import settings
import recording

@task
def fetch_recordings():
    util.lnp("Fetching schedule..")
    return recording.load_from_web()

@task
def record(r):
    util.lnp("recording %s" % r.data['title'])
    r.record()
    while not r.complete():
        time.sleep(10)
    r.tag()
    util.lnp("tagging %s" % r.data['title'])

@task
def clean():
    def do_directory(p):
        contents = os.listdir(p)
        for f in contents:
            if os.path.isfile(os.path.join(p,f)):
                do_file(p,f)
            elif os.path.isdir(os.path.join(p,f)):
                do_directory(os.path.join(p,f))
        if len(contents) == 0:
            subprocess.Popen(['rm','-r',p]).wait()
    def do_file(p,f):
        l = f.split('-')
        if len(l) >= 3:
            d = datetime(int(l[2]),int(l[0]),int(l[1]))
            now = datetime.today()
            if now-d > timedelta(days=120):
                util.lnp("Removing %s/%s" % (p,f))
                subprocess.Popen(['rm',f],cwd=p).wait()
    do_directory(settings.OUTPUT_DIR)        

@task
def fingerprint_stream():
    # I actually modified icecream so it takes seconds as an arg. Booya.
    now = datetime.today()
    util.lnp("Fingerprinting stream...")
    controls = {'file': now.strftime(settings.FILENAME),
                'runtime': '1min', 
               }
    controls['filemp3'] = controls['file']+".mp3"
    od = "/tmp/"
    call = lambda x: Template(x).substitute(controls)
    cmd = map(call,settings.RIPPER_COMMAND)
    subprocess.Popen(cmd,cwd=od).wait()
    #Now we call the echoprint software...
    cmd = map(call,settings.ECHOPRINT_COMMAND)
    (stdout,stderr) = subprocess.Popen(cmd,cwd=od,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
    #Now, what we should see in stdout is some json with the current song:
    util.lnp(stdout)
    js = json.loads(stdout)
    util.lnp(json.dumps(js))
    subprocess.Popen(['rm',controls['filemp3']], cwd=od)
    #data = urllib.urlencode({'query':json.dumps(js)})
    #Pack it up, and send it to the server
    url = Template(settings.ECHONEST_QUERYURL).substitute({'apikey':settings.ECHONEST_KEY,'code':js[0]['code']})
    util.lnp(url)
    r = urllib2.urlopen(url)
    util.lnp(r.read())
