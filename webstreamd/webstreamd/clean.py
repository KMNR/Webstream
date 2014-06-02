import subprocess
import sys
import os
from datetime import datetime, timedelta

from settings import Settings

settings = Settings()

def do_directory(p):
    contents = os.listdir(p)
    for f in contents:
        if os.path.isfile(os.path.join(p,f)):
            do_file(p,f)
        elif os.path.isdir(os.path.join(p,f)):
            do_directory(os.path.join(p,f))
    if len(contents) == 0:
        subprocess.Popen(['rm','-r',p]).wait()

def do_file(p,f):
    (bn, _) = os.path.splitext(f)
    l = bn.split('-')
    if len(l) >= 4:
        d = datetime(int(l[1]),int(l[2]),int(l[3]))
        now = datetime.today()
        if now-d > timedelta(days=settings.KEEPFOR):
            print "Removing {}/{}".format(p,f)
            subprocess.Popen(['rm',f],cwd=p).wait()

def main():
    if len(sys.argv) == 2:
        conf_file = sys.argv[1]
    elif len(sys.argv) == 1:
        conf_file = Settings.DEFAULTCONFIG
    else:
        print "Format: {} [CONFIG_FILE]".format(sys.argv[0])
        exit(1)
    settings.load_config(conf_file)
    do_directory(settings.RECORDINGDIR)

if __name__ == "__main__":
    main()        
