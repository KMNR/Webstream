import subprocess
import sys
import os

# This script executes the actual recoring: It makes the directories needed
# and calls icecream to do the recording.

def main():
     
    if len(sys.argv) != 4:
        print "Usage: {} FILE DURATION STREAM".format(sys.argv[0])
        print "Where DURATION is in minutes."
        print "Where FILE does not include the file extension, but may include C date codes"
        exit(1)

    targetdir = os.path.dirname(sys.argv[1])
    targetfile = os.path.basename(sys.argv[1])
    scriptdir = os.path.dirname(__file__)

    subprocess.call(["mkdir","-p",format(targetdir)])
    os.chdir(targetdir)
    subprocess.call(["perl", "{}/icecream.pl".format(scriptdir),
                     "--name={}".format(targetfile),
                     "--stop={}min".format(sys.argv[2]),
                     "-q", "{}".format(sys.argv[3])])

if __name__ == "__main__":
    main()
