import subprocess
import sys
import os

# This script executes the actual recoring: It makes the directories needed
# and calls icecream to do the recording.

scriptdir = os.path.dirname(__file__)

print scriptdir
 
if len(sys.argv) != 4:
	print "Usage: {} FILE DURATION STREAM".format(sys.argv[0])
	print "Where DURATION is in minutes."
	print "Where FILE does not include the file extension, but may include C date codes"
    exit(1)

targetdir = os.path.dirname(sys.argv[1])

subprocess.call("mkdir -p {}".format(targetdir))
subprocess.call("perl {}/icecream.pl --name='{}' --stop='{}min$' -q {}".format(
    scriptdir, sys.argv[1], sys.argv[2], sys.argv[3])
