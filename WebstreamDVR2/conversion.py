from datetime import *
import urllib2
import json
from settings import *

def convert_schedule(jsondata):
    return [ convert_show(show) for show in jsondata ] 

def convert_dow_to_iso(inp):
    d = {'Mo':1,
         'Tu':2,
         'We':3,
         'Th':4,
         'Fr':5,
         'Sa':6,
         'Su':7 }
    return d[inp]

def convert_timeslot_to_duration(inp):
    """
    Converts the schedule duration notation to a timedelta object
    """
    time_format = "%H:%M:%S"
    start_time = datetime.strptime(inp['start_time'],time_format)
    end_time = datetime.strptime(inp['end_time'],time_format)
    if end_time < start_time:
        end_time += timedelta(days=1)
    return end_time - start_time

def convert_show(indict):
    """
    Converts the KMNR API to the WebstreamDVR standardized format:

    id - A unique identifier for this recording
    title - show title
    genres - The genres of the show
    djs - a string of the people who run the show
    start_day - ISO weekday (1 for monday, 7 for sunday.)
    start_time - The time that the show starts in the format (HH:MM:SS)
    duration - The duration of the show in seconds.
    
    returns a dictionary that is converted to JSON
    """

    if 'djs' in indict:
        djlist = ", ".join([ x['name'] for x in indict['djs'] ])
    else:
        djlist = ""

    outdict = {
        'title': indict['title'],
        'genres': indict['genres'],
        'djs': djlist,
        'start_day': convert_dow_to_iso(indict['time_slot']['day']),
        'start_time': indict['time_slot']['start_time'],
        'duration': convert_timeslot_to_duration(indict['time_slot']).total_seconds(),
        'id': indict['id']
        }
    return outdict

def main():
    """
    Load a schedule from the web, convert each entry to the new format,
    print the result in json.
    """
    f = urllib2.urlopen(SCHEDULE_URL)
    schedule =json.loads(f.read())
    converted = convert_schedule(schedule)
    print json.dumps(converted)

if __name__ == "__main__":
    main()
