#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------
# Copyright The IETF Trust 2018, All Rights Reserved
# --------------------------------------------------

from __future__ import unicode_literals, print_function, division

import os

from codecs import open
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(here, 'README.md'), encoding='utf-8') as file:
    long_description = file.read()

setup(
    name='svgcheck',

    description="Verify that an svg file is compliant with the RFC standards.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # The projects main homepage.
    url='https://github.com/ietf-tools/svgcheck/',

    # Author details
    author='Jim Schaad',
    author_email='ietf@augustcellars.com',

    # Choose your license
    license='Simplified BSD',

    # Classifiers
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Other Audience',
        'Topic :: Text Processing',
        'Topic :: Text Processing :: Markup :: XML',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        ],

    # What does your project relate to?
    keywords='svg validation RFC',

    #
    packages=find_packages(exclude=['contrib', 'docs', 'Tests']),

    # List run-time dependencies here.
    install_requires=requirements,
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4',

    # List additional gorups of dependencies here.
    # extras_require=(
    #  'dev':['twine',],
    # ]

    # package_data={
    #    'svgcheck': ['run.py']
    #    },

    entry_points={
        'console_scripts': [
            'svgcheck=svgcheck.run:main'
            ]
        },
    zip_safe=False
)
