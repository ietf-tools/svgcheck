<div align="center">
    
<img src="https://raw.githubusercontent.com/ietf-tools/common/main/assets/logos/svgcheck.svg" alt="SVGCHECK" height="125" />
    
[![Release](https://img.shields.io/github/release/ietf-tools/svgcheck.svg?style=flat&maxAge=360)](https://github.com/ietf-tools/svgcheck/releases)
[![License](https://img.shields.io/github/license/ietf-tools/svgcheck)](https://github.com/ietf-tools/svgcheck/blob/main/LICENSE)
[![PyPI - Version](https://img.shields.io/pypi/v/svgcheck)](https://pypi.org/project/svgcheck/)
[![PyPI - Status](https://img.shields.io/pypi/status/svgcheck)](https://pypi.org/project/svgcheck/)
[![PyPI - Format](https://img.shields.io/pypi/format/svgcheck)](https://pypi.org/project/svgcheck/)
    
##### Check SVG against RFC schema
    
</div>

- [Changelog](https://github.com/ietf-tools/svgcheck/blob/main/CHANGELOG.md)
- [Contributing](https://github.com/ietf-tools/.github/blob/main/CONTRIBUTING.md)

---

This program takes an XML file containing an SVG or an RFC document.  It then compares all of the SVG elements with the schema defined in the document with [RFC 7996 bis](https://datatracker.ietf.org/doc/draft-7996-bis). The program has the option of modifying and writing out a version of the input that passes the defined schema.


## Usage

`svgcheck` accepts a single XML document as input and optionally outputs a modified version of the document.

### Basic Usage

```sh
svgcheck [options] SOURCE
```

### Options

| Short         | Long             | Description                                                                       |
|---------------|------------------|-----------------------------------------------------------------------------------|
| `-C`          | `--clear-cache`  | purge the cache and exit                                                          |
| `-h`          | `--help`         | show the help message and exit                                                    |
| `-N`          | `--no-network`   | don't use the network to resolve references                                       |
| `-q`          | `--quiet`        | dont print anything                                                               |
| `-r`          | `--repair`       | repair the SVG so it meets RFC 7966, only emit the new file if repairs are needed |
| `-a`          | `--always-emit`  | repair the SVG file if needed, emit the file even if no repairs are needed        |
| `-v`          | `--verbose`      | print extra information                                                           |
| `-V`          | `--version`      | display the version number and exit                                               |
| `-d RNG`      | `--rng=RNG`      | specify an alternate RNG file                                                     |
| `-o FILENAME` | `--out=FILENAME` | specify an output filename, default to stdout                                     |
| `-g`          | `--grey-scale`   | use a grey scale heuristic to determine what is white                             |
|               | `--grey-level`   | cut off level between black and white                                             |

## Dependencies

`svgcheck` depends on the following packages:

- [lxml](http://lxml.de) *(>= 4.1.1)*
- [xml2rfc](https://github.com/ietf-tools/xml2rfc/) *(>= 3.16.0)*
