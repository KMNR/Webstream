from datetime import timedelta
import ConfigParser

class Settings(object)
    DEFAULTCONFIG = "/etc/webstream.d/webstream.conf"
    
    
    def __init__(self):
        pass
    
    def load_config(self, conf_file)
       config = ConfigParser.RawConfigParser()
       config.read(conf_file)
       
       self.STREAMURL = config.get("stream", "stream_url")
       self.LEADIN = timedelta(minutes=config.getint("recording", "leadin"))
       self.LEADOUT = timedelta(minutes=config.getint("recording", "leadout"))
       self.RECORDINGDIR = config.get("recording", "directory")
       self.SCHEDULE = config.get("schedule", "schedule")