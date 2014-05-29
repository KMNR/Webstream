from datetime import timedelta

SCHEDULE_URL = "http://kmnr.org/api/schedule/"
LEADIN = timedelta(minutes=5)
LEADOUT = timedelta(minutes=5)
STREAM_URL = "http://marconi.kmnr.org:7000/webstream-local.mp3"
RECORDER_FOLDER = "/mnt/ass/{show}/"
RIPPER_COMMAND = "icecream --name='{target}{show}-%Y-%m-%d' --stop='{duration}min' -q {stream}"
