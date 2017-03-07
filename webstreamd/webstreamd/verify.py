"""
@author Doug McGeehan <djmvfb@mst.edu>

Verify that shows in the current schedule are actually being recorded.

Currently, this script only works if you have a symbolic link to the
neighboring 'webstreamd' directory.
"""

import json
from webstreamd.crontab import safename
import sys
import os
import urllib


KMNR_ORG_SCHEDULE_URL = 'https://kmnr.org/api/schedule/'
SHOW_RECORDINGS_DIR = '/var/www/'


def _print_summary(show):
    print(show['title'].encode('utf-8'))
    show_DJs = [dj['name'] for dj in show['djs']]
    print('{djs}'.format(djs=' '.join(show_DJs)))
    print('Stored in {}'.format(os.path.join(SHOW_RECORDINGS_DIR,
                                             safename(show['title']))))
    print('.'*80)


def main():
    schedule_raw = _load_schedule()
    shows = json.loads(schedule_raw)
    print('{} shows are defined in the schedule'.format(len(shows)))

    non_existent_shows = []
    for show in shows:
        if not _verify_exists(show=show['title'], within=SHOW_RECORDINGS_DIR):
            _print_summary(show=show)
            non_existent_shows.append(show)

    print('-'*80)
    print('{0} shows are not currently recorded (out of {1})'.format(
        len(non_existent_shows),
        len(shows)
    ))
    # show_titles = [show['title'] for show in non_existent_shows]
    # print('\t{}'.format('\n\t'.join(show_titles)))



def _load_schedule():
    '''
    Retrieve the show schedule in JSON format, either from KMNR.org or from
    the specified file.
    '''
    if len(sys.argv) < 2:
        # no show schedule file was provided as input
        # retrieve it from kmnr.org
        print('Downloading schedule from {}'.format(KMNR_ORG_SCHEDULE_URL))
        response = urllib.urlopen(KMNR_ORG_SCHEDULE_URL)
        data = response.read()
        text = data.decode('utf-8')

    else:
        schedule_file = sys.argv[1]
        assert os.path.isfile(schedule_file), 'No file located at {}'.format(
            schedule_file
        )

        print('Loading schedule from {}'.format(schedule_file))
        with open(schedule_file) as f:
            text = f.read()

    return text


def _verify_exists(show, within):
    show_recording_directory = safename(show)
    return os.path.isdir(os.path.join(SHOW_RECORDINGS_DIR,
                                      show_recording_directory))


if __name__ == '__main__':
    main()

