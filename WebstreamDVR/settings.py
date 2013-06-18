from datetime import timedelta
from secret import *

STREAM_URL = "http://marconi.kmnr.org:7000/webstream-local.mp3"
SCHEDULE_URL = "http://kmnr.org/api/schedule/"
RIPPER_COMMAND = ["icecream","--name=$file","--stop=$runtime","--debug","-q",STREAM_URL]
TAGGER_COMMAND = ["id3tag","--artist=$djs","--song=$start","--album=$title","$filemp3"]
OUTPUT_DIR = "/mnt/ass/www/"
FILENAME = "%m-%d-%Y-%s"
RECORDING_RUNUP = timedelta(minutes=5)
RECORDING_WINDDOWN = timedelta(minutes=10)
