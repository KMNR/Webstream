from multiprocessing import Process, Queue
import time
from datetime import datetime, timedelta

import recording
import util
import tasks

def main():
    p = None
    q = Queue()
    rt = []
    recordings = []
    fetch_task = None
    next_pull = None
    clean_task = None
    next_clean = None
    while 1:
        if clean_task == None and (next_clean == None or next_clean < datetime.today()):
            clean_task = tasks.clean.delay()
            next_clean = datetime.today() + timedelta(minutes=30)
            util.lnp("Next clean at %s" % str(next_clean))
    	elif clean_task != None:
            if clean_task.status == 'FAILURE':
                util.lnp("Cleaning Failed")
                clean_task = None
            elif clean_task.status == 'SUCCESS':
                util.lnp("Cleaning Worked!")
                clean_task = None
                 
        if fetch_task == None and (next_pull == None or next_pull < datetime.today()):
            fetch_task = tasks.fetch_recordings.delay()
            util.lnp("Fetching schedule")
        elif fetch_task != None:
            if fetch_task.status == 'FAILURE':
                util.lnp("Couldn't fetch schedule")
                fetch_task = None
            elif fetch_task.status == 'SUCCESS':
                recordings = fetch_task.result
                fetch_task = None
                next_pull = datetime.today() + timedelta(minutes=15)
                util.lnp("Next Update: %s" % next_pull)
                util.lnp("Loaded %s shows" % len(recordings))
		for r in recordings:
		    util.lnp("%s - %s" % (r.data['title'],r.next_recording()))
        
        for r in recordings:
            if r.ready() and r.id not in [ t[0] for t in rt ]:
                rt.append((r.id,tasks.record.delay(r)))
                util.lnp("Recording %s" % r.data['title'])
                time.sleep(60)

        if len(rt) > 0 and rt[0][1].ready():
            util.lnp("Cleaning up thread...");
            rt.pop(0)
            util.lnp("Done!")

        time.sleep(1) 
if __name__ == "__main__":
    main()
