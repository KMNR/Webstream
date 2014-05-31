from datetime import *
import json
import sys
from settings import *

def get_current_show(js):
    """
    Given a schedule in the converted format
    
    Get the current show 
    """
    now = datetime.today()
    # Filter out shows that aren't today.
    js = [ x for x in js if x['start_day'] == now.isoweekday() ]
    
    for show in js:

        d = timedelta(seconds=show['duration'])
        time_format = "%H:%M:%S"
        start_time = datetime.strptime(show['start_time'],time_format)
        end_time = start_time + d
        
        start_time -= LEADIN
        end_time += LEADOUT

        start_time = datetime.combine(date.today(),start_time.time())
        end_time = datetime.combine(date.today(),end_time.time())
        if now >= start_time and now <= end_time:
            return show

def main():
    js = json.load(sys.stdin)
    print get_current_show(js)

if __name__ == "__main__":
    main()
