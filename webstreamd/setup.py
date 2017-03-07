##############################################################################
#
# Copyright (c) 2014 Stephen Jackson
# All Rights Reserved.
#
##############################################################################

import os
import sys

py_version = sys.version_info[:2]

if py_version < (2, 6):
    raise RuntimeError('On Python 2, Supervisor requires Python 2.6 or later')
elif (3, 0) <= py_version:
    raise RuntimeError('Not for Python 3 (yet)')

requires = []
tests_require = []
    
from setuptools import setup, find_packages
here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except:
    README = """\
Webstreamd is a utility for recording webstream according to a schedule\
"""
    CHANGES = ''

CLASSIFIERS = [
    'Topic :: System :: Monitoring',
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7"
]

version_txt = os.path.join(here, 'webstreamd/version.txt')
webstreamd_version = open(version_txt).read().strip()

dist = setup(
    name='webstreamd',
    version=webstreamd_version,
    license='',
    url='http://kmnr.org',
    description="A utility to automate recording webstreams based on a schedule",
    long_description=README + '\n\n' +  CHANGES,
    classifiers=CLASSIFIERS,
    author="Stephen Jackson",
    author_email="scj7t4@mst.edu",
    maintainer="Stephen Jackson",
    maintainer_email="scj7t4@mst.edu",
    packages=find_packages(),
    install_requires=requires,
    extras_require={},
    tests_require=tests_require,
    include_package_data=True,
    zip_safe=False,
    data_files=[('/etc/webstream.d',['webstreamd/skel/webstream.d/webstreamd.conf.example']),
                ('/etc/cron.d',['webstreamd/skel/cron.d/webstreamd.example']),
                ('webstreamd',['webstreamd/icecream.pl'])],
    entry_points={
     'console_scripts': [
         'webstreamd-crontab = webstreamd.crontab:main',
         'webstreamd-kmnr = webstreamd.converters.kmnr:main',
         'webstreamd-clean = webstreamd.clean:main',
         'webstreamd-record = webstreamd.record:main',
         'webstreamd-verify = webstreamd.verify:main',
        ],
    },
)
