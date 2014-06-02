#!/bin/bash

# This script executes the actual recoring: It makes the directories needed
# and calls icecream to do the recording. It uses exec to avoid a subshell
# so that fewer processes are running.

if [ $# -ne 4 ]; then
	echo "Usage: {} FILE DURATION STREAM".format(sys.argv[0])
	echo "Where DURATION is in minutes."
	echo "Where FILE does not include the file extension, but may include C date codes"
fi
	
export TARGETDIR=$(dirname ${1})
export SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

mkdir -p ${TARGETDIR}
exec ${SCRIPTDIR}/icecream.pl --name='${1}' --stop='${2}min$' -q ${3}