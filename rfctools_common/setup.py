#!/usr/bin/env python
# --------------------------------------------------
# Copyright The IETF Trust 2018-2019, All Rights Reserved
# --------------------------------------------------

import re
from setuptools import setup, find_packages
from codecs import open
from os import path
import rfctools_common
import six

if six.PY3:
    unicode = str

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as file:
    long_description = file.read()
    long_description = long_description.replace('\r', '')

# Get the requirements from the local requirements.txt file
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as file:
    requirements = file.read().splitlines()

# Get additional items from the local MANIFEST.in file
with open(path.join(here, 'MANIFEST.in'), encoding='utf-8') as file:
    extra_files = [l.split()[1] for l in file.read().splitlines() if l]


def parse(changelog):
    ver_line = "^([a-z0-9+-]+) \(([^)]+)\)(.*?) *$"
    sig_line = "^ ?-- ([^<]+) <([^>]+)>  (.*?) *$"

    entries = []
    if isinstance(changelog, str) or isinstance(changelog, unicode):
        changelog = open(changelog, mode='rU', encoding='utf-8')
    for line in changelog:
        if re.match(ver_line, line):
            package, version, rest = re.match(ver_line, line).groups()
            entry = {}
            entry["package"] = package
            entry["version"] = version
            entry["logentry"] = ""
        elif re.match(sig_line, line):
            author, email, date = re.match(sig_line, line).groups()
            entry["author"] = author
            entry["email"] = email
            entry["datetime"] = date
            entry["date"] = " ".join(date.split()[:3])

            entries += [entry]
        else:
            entry["logentry"] += line.rstrip() + '\n'
    changelog.close()
    return entries


changelog_entry_template = """
Version %(version)s (%(date)s)
------------------------------------------------

%(logentry)s

"""

long_description += """
Changelog
=========

""" + "\n".join([changelog_entry_template % entry for entry in parse("changelog")[:3]])

long_description = long_description.replace('\r', '')

setup(
    name='rfctools_common',

    # Versions should comply with PEP440.
    version=rfctools_common.__version__,

    description="Verify that an svg file is compliant with the RFC standards.",
    long_description=long_description,

    # The projects main homepage.
    url='https://tools.ietf.org/tools/ietfdb/browser/brance/elft/svgcheck/',

    # Author details
    author='Jim Schaad',
    author_email='ietf@augustcellars.com',

    # Choose your license
    license='Simplified BSD',

    # Classifiers
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Other Audience',
        'Topic :: Text Processing',
        'Topic :: Text Processing :: Markup :: XML',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.7',
    ],

    # What does your project relate to?
    keywords='RFC common',

    #
    packages=find_packages(exclude=['contrib', 'docs', 'Tests']),

    # List run-time dependencies here.
    install_requires=requirements,
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4',

    # List additional gorups of dependencies here.
    # extras_require=(
    #  'dev':['twine',],
    # ]

    package_data={
        'rfctools-common': ['templates/*']
    },
    include_package_data=True,

    zip_safe=False
)
