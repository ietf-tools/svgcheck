# Test Directory for RFClint

This directory contains all of the automated tests that are part of the check-in suite for RFClint.

# Test Format

The tests are all identified by a file name ending in '.json'.
The format of the test driver file can be found in the test directory

# Test Groupings

The test groups are as follows:
* Malformed XML tests
* Wellformed XML tests
* RNG validation tests
* Spelling tests
* Duplicate word detection tests
* ABNF tests
* XML stanza testing

## Malformed XML tests

Malformed tests should be named malform##.json.

Tests:
* Malformed file
* Malformed entity
* Malformed xinclude
* Can't find xinclude and trying too

## Well formed XML tests

Tests:
* Xinclude tests
* SVG href tests
* SVG file tests

## RNG validation tests

RNG validation tests should be named rng##.json

Tests:
* Xinclude not resolved
* Invalid schema file
* Invalid schema in entity
* Invalid schema in xinclude
* Invalid schema in href='data:..."


