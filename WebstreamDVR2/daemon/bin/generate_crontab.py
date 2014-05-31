from datetime import *
import json
import sys
from settings import *

def safename(s):
    return ''.join(e for e in s if e.isalnum())

def add_leaders(show):
    """
    Adds extra buffer to the show to keep the extras from overwhelming the
    recordings.
    """
    # Increase the duration to add the leadin and leadout
    show['duration'] + LEADIN.total_seconds() + LEADOUT.total_seconds()

    # Adjust the start time
    time_format = "%H:%M:%S"
    start_time = datetime.strptime(show['start_time'],time_format)
    start_time -= LEADIN
    
    # Store the adjusted time
    show['start_time'] = str(start_time.time())
    
    return show

def show_to_crontab(show): 
    time_format = "%H:%M:%S"
    start_time = datetime.strptime(show['start_time'],time_format)
    cronline = "{min} {hour} {dom} {mon} {dow} {command}"
    rd = {
        'target': RECORDER_FOLDER,
        'stream': STREAM_URL,
        'show': safename(show['title']),
        'duration': show['duration']/60.0
        }
    cmd = RIPPER_COMMAND.format(**rd)
    cd = {
        'min': start_time.minute,
        'hour': start_time.hour,
        'dom': '*',
        'mon': '*',
        'dow': show['start_day'] % 7,
        'command': cmd
        }
    return cronline.format(**cd)

def generate_crontab(js):
    for show in js:
        print show_to_crontab(show)

def main():
    js = json.load(sys.stdin)
    js = [ add_leaders(x) for x in js ]
    generate_crontab(js)

if __name__ == "__main__":
    main()
