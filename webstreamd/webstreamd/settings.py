from datetime import timedelta
import ConfigParser

class Settings(object):
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
        self.SCHEDULE = config.get("schedule", "schedule")
