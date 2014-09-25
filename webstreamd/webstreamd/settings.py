"""
@author Stephen Jackson <scj7t4@mst.edu>

This loads a configuration file
"""
from datetime import timedelta
import ConfigParser

class Settings(object):
    """
    Configuration Options:
    
    stream/streamurl : The location of the stream that will be recorded. In
        theory this can be a .pls or .m3u stream url.
    recording/leadin : The amount of time in minutes that will be recorded
        before the show is scheduled to start (for early starts etc)
    recording/leadout : The amount of time in minutes that will be recorded
        after the show is scheduled to end (for run-over etc)\
    recording/directory : The directory where the recordings will be made.
    recording/keepfor : The number of days that you will keep the recording
        for in days.
    schedule/schedule : The location of the schedule json file.
    """
    DEFAULTCONFIG = "/etc/webstream.d/webstreamd.conf" 
    
    def __init__(self):
        pass
    
    def load_config(self, conf_file):
        config = ConfigParser.RawConfigParser()
        fp = open(conf_file)
        config.readfp(fp)
        fp.close()
       
        self.STREAMURL = config.get("stream", "streamurl")
        self.LEADIN = timedelta(minutes=config.getint("recording", "leadin"))
        self.LEADOUT = timedelta(minutes=config.getint("recording", "leadout"))
        self.RECORDINGDIR = config.get("recording", "directory")
        self.KEEPFOR = config.getint("recording","keepfor")
        self.SCHEDULE = config.get("schedule", "schedule")
