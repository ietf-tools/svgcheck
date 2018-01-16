#!/usr/bin/env python
# --------------------------------------------------
# Copyright The IETF Trust 2018, All Rights Reserved
# --------------------------------------------------

import re
import sys
from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as file:
    long_description = file.read()

# Get the requirements from the local requirements.txt file
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as file:
    requirements = file.read().splitlines()
major, minor = sys.version_info[:2]
if major == 2:
    requirements.append("subprocess32")

# Get additional items from the local MANIFEST.in file
with open(path.join(here, 'MANIFEST.in'), encoding='utf-8') as file:
    extra_files = [ l.split()[1] for l in file.read().splitlines() if l ]

import rfclint

setup(
    name='rfclint',

    # Versions should comply with PEP440.
    version=rfclint.__version__,

    description="Perform a set of checks on an RFC input file to check for errors.",
    long_description=long_description,
    
    # The projects main homepage.
    url='https://tools.ietf.org/tools/ietfdb/browser/brance/elft/rfclint/',

    # Author details
    author='Jim Schaad',
    author_email='ietf@augustcellars.com',

    # Choose your license
    license='Simplified BSD',

    # Classifiers
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Other Audience',
        'Topic :: Text Processing',
        'Topic :: Text Processing :: Markup :: XML',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        ],

    # What does your project relate to?
    keywords='validation RFC internet-draft',

    #
    packages=find_packages(exclude=['contrib', 'docs', 'Tests']),

    # List run-time dependencies here.
    install_requires=requirements,
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, <4',

    # List additional gorups of dependencies here.
    # extras_require=(
    #  'dev':['twine',],
    # ]

    # package_data={
    #    'svgcheck': ['run.py']
    #    },
    package_data={
#        ':platform_system == "win32"': [ "win32/*" ],
        'rfclint': [ "../win32/bap.exe", "../win32/cygwin1.dll" ],
    },
            

    entry_points={
        'console_scripts': [
            'rfclint=rfclint.run:main'
            ]
        },
    include_package_data = True,
    zip_safe=False
)
