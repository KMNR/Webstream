from datetime import datetime,date,timedelta
import time
import os
from string import Template
import urllib2
import json
import subprocess
import os
import re

import settings

def titlecase(s):
    return re.sub(r"[A-Za-z]+('[A-Za-z]+)?",
        lambda mo: mo.group(0)[0].upper() +
		   mo.group(0)[1:].lower(),s)

def alphas(s):
    return ''.join(e for e in s if e.isalnum())

class Recording(object):
    def __init__(self,show_obj):
        """
        Initializes the recording object, initialized from a show_obj dictionary.
        """

        self.data = {}
        self.data['title'] = show_obj['title']
        self.data['djs'] = ",".join([ x['name'] for x in show_obj['djs'] ])
        if len(self.data['djs']) == 0 and show_obj['genres']:
            self.data['djs'] = show_obj['genres']
            self.data['genres'] = ""
        else:
            self.data['genres'] = show_obj['genres']
        time_format = "%H:%M:%S"
        self.start_time = datetime.strptime(show_obj['time_slot']['start_time'],time_format)
        self.start_time = self.start_time.time()
        self.end_time = datetime.strptime(show_obj['time_slot']['end_time'],time_format)
        self.end_time = self.end_time.time()
        dow_convert = {'Su':6,'Mo':0,'Tu':1,'We':2,'Th':3,'Fr':4,'Sa':5}
        self.day = dow_convert[show_obj['time_slot']['day']]
        self.process = None
        self.id = show_obj['id']
        self.output_file = None
     
    def next_recording(self):
        recording_start = datetime.combine(date.today(),self.start_time)
        # Shift the day until it lines up with the day the show is on.
        for i in range(8):
            if recording_start.weekday() == self.day and datetime.today() < recording_start:
                break
            recording_start += timedelta(days=1)
        return recording_start       
     
    def ready(self):
        #Calculate the duration of the show
        now = datetime.today()
        time_til_start = self.next_recording() - now
        if not self.recording() and time_til_start < settings.RECORDING_RUNUP:
            return True
        else:
            return False
    
    def record(self,force=False):
        if not self.ready() and force == False:
            return
        
        print "Record called"
        od = os.path.join(settings.OUTPUT_DIR,alphas(titlecase(self.data['title'])))
        print "Making %s" % od
        subprocess.call(['mkdir','-p',od])
        fp = settings.FILENAME
        self.output_file = time.strftime(fp)
        self.data['file'] = self.output_file
        self.data['filemp3'] = self.output_file+".mp3"
        tmp_end = datetime.combine(date.today(), self.end_time)
        tmp_start = self.next_recording()
        if tmp_end < tmp_start:
            tmp_end += timedelta(days = 1)
        print "%s < %s" % (tmp_end,tmp_start)
        duration  = (tmp_end - tmp_start)
        now = datetime.today()
        time_til_start = tmp_start - now
        self.data['start'] = tmp_start.date()
        duration += time_til_start + settings.RECORDING_WINDDOWN
        duration_minutes = int(duration.total_seconds() / 60)
        if int(duration.total_seconds()) % 60 > 0:
            duration_minutes += 1
        self.data['runtime'] = "%smin" % duration_minutes
        call = lambda x: Template(x).substitute(self.data)
        cmd = map(call,settings.RIPPER_COMMAND)
        print cmd
        self.process = subprocess.Popen(cmd,cwd=od)

    def recording(self):
        if self.process == None:
            return False
        if self.process.poll() == None:
            return True
        return False
    
    def complete(self):
        if self.process != None and not self.recording():
            return True
        return False

    def tag(self):
        if not self.complete():
            return
        od = os.path.join(settings.OUTPUT_DIR,alphas(titlecase(self.data['title'])))
        call = lambda x: Template(x).substitute(self.data)
        subprocess.Popen(map(call,settings.TAGGER_COMMAND),cwd=od).wait()
    
    def __cmp__(self,other):
        if self.id == other.id:
            return True
        else:
            return False

def load_from_file():
    f = open('schedule.json')
    schedule = json.loads(f.read())
    recordings = [ Recording(s) for s in schedule ]
    return recordings

def load_from_web():
    f = urllib2.urlopen(settings.SCHEDULE_URL)
    schedule =json.loads(f.read())
    recordings = [ Recording(s) for s in schedule ]
    return recordings

def main():
    recordings = load_from_web()
    for r in recordings:
        print "%s %s: %s %s" % (r.id,r.day,r.next_recording(),r.data['title'])
    
if __name__ == "__main__":
    main()
