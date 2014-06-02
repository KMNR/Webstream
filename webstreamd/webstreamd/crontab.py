from datetime import *
import json
import sys
import os
from settings import Settings

settings = Settings()

def safename(s):
    return ''.join(e for e in s if e.isalnum())

def add_leaders(show):
    """
    Adds extra buffer to the show to keep the extras from overwhelming the
    recordings.
    """
    # Increase the duration to add the leadin and leadout
    show['duration'] += Settings.LEADIN.total_seconds() 
    show['duration'] += Settings.LEADOUT.total_seconds()

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
    file = "{target}{show}/{show}-%Y-%m-%d".format(target=RECORDER_FOLDER,
        show=safename(show['title']))
        
    script = os.path.join(os.path.dirname(__file__),"record.sh")
    rd = {
        'script': 
        'file': file,
        'stream': STREAM_URL,
        'duration': show['duration']/60.0
        }
    recorder_cmd = "/bin/bash {script} {file} {duration} {stream}"
    
    cmd = recorder_cmd.format(**rd)
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

def main(conf_file):
    settings.load_config(conf_file)
    js = json.load(sys.stdin)
    js = [ add_leaders(x) for x in js ]
    generate_crontab(js)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        conf_file = sys.argv[1]
    elif len(sys.argv) == 1:
        print "Using default config {}".format(Settings.DEFAULTCONFIG)
        conf_file = Settings.DEFAULTCONFIG
    else:
        print "Format: {} [CONFIG_FILE]".format(sys.argv[0])
        exit(1)
    main(conf_file)
