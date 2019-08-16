#!/usr/bin/env python
# ----------------------------------------------------
# Copyright The IETF Trust 2018-9, All Rights Reserved
# ----------------------------------------------------

import re
import sys
from setuptools import setup, find_packages
from codecs import open
from os import path
from setuptools.command.install import install
import os
import rfclint

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as file:
    long_description = file.read()
    long_description = long_description.replace('\r', '')

# Get the requirements from the local requirements.txt file
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as file:
    requirements = file.read().splitlines()
major, minor = sys.version_info[:2]
if major == 2:
    requirements.append("subprocess32")

# Get additional items from the local MANIFEST.in file
with open(path.join(here, 'MANIFEST.in'), encoding='utf-8') as file:
    extra_files = [l.split()[1] for l in file.read().splitlines() if l]


class PostInstallCommand(install):
    def run(self):
        # install.run(self)
        install.do_egg_install(self)
        if os.name == "nt":
            return
        xx = self.which('bap')
        if xx:
            st = os.stat(xx)
            os.chmod(xx, st.st_mode | 0o111)

    def is_exists(self, fpath):
        return os.path.isfile(fpath)

    def which(self, program):

        fpath, fname = os.path.split(program)
        if fpath:
            if self.is_exists(program):
                return program
        else:
            for pathX in os.environ["PATH"].split(os.pathsep):
                exe_file = os.path.join(pathX, program)
                if self.is_exists(exe_file):
                    return exe_file
        return None


def parse(changelog):
    ver_line = "^([a-z0-9+-]+) \(([^)]+)\)(.*?) *$"
    sig_line = "^ ?-- ([^<]+) <([^>]+)>  (.*?) *$"

    entries = []
    if isinstance(changelog, type('')):
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
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Other Audience',
        'Topic :: Text Processing',
        'Topic :: Text Processing :: Markup :: XML',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        ],

    # What does your project relate to?
    keywords='validation RFC internet-draft',

    #
    packages=find_packages(exclude=['contrib', 'docs', 'Tests']),

    # List run-time dependencies here.
    install_requires=requirements,
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4',

    # List additional groups of dependencies here.
    # extras_require=(
    #  'dev':['twine',],
    # ]

    # package_data={
    #    'svgcheck': ['run.py']
    #    },
    # package_data={
    #        ':platform_system == "win32"': [ "win32/*" ],
    # 'rfclint': [ "../win32/bap.exe", "../win32/cygwin1.dll" ],
    # },
    # Match with what is in abnf.py
    # data_files=[('bin',
    #             ["win32/bap.exe", "win32/cygwin1.dll"] if os.name == "nt" else
    #             ["linux/bap"] if sys.platform.startswith("linux") else
    #             ["macos/bap"] if sys.platform == "darwin" else []
    #             )
    #            ],
    # cmdclass= {
    #    'install': PostInstallCommand
    # },

    entry_points={
        'console_scripts': [
            'rfclint=rfclint.run:main'
            ]
        },
    include_package_data=True,
    zip_safe=False
)
