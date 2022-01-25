# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.19] - 2019-08-29

### Changed
- Move sources to an appropirate github location
- Always emit a file when repair is chosen

## [0.5.17] - 2019-08-16

### Removed
- Remove Python 3.4 from the supported list

## [0.5.16] - 2019-07-01

### Changed

- Require new version of rfctools for new RNG file

## [0.5.15] - 2019-05-27

### Added

- Add test case for UTF-8
- Add test case for two pass

### Changed

- Fix errors where we need to emit UTF-8 characters in either text or attributes
- Force DOCTYPE not to be emitted when we have fixed a file so that we don't pick up default attributes

## [0.5.14] - 2019-04-21

### Changed

- Force a viewBox to be part of the output

## [0.5.13] - 2019-04-06

### Changed

- Setup so that it can take input from stdin
- Clean up so that pyflakes passes

## [0.5.12] - 2019-02-22

### Added

- Add exit comment on success/Failure

### Changed

- Copy the preserve whitespace parameter from rfclint. This preserves formatting.
- Preserve comments when doing a repair
- Change the test scripts to use the same parsing options

## [0.5.4] - 2018-05-09

### Added

- Add the numeric values for font-weight

### Changed

- Allow for #fff to be tagged as white. Original discussions thought this was not going to be used.

## [0.5.1] - 2018-03-04

### Added

- Setup things so it publishes to PyPI

## [0.5.0] - 2018-02-25

- No changes

## [0.0.3] - 2018-02-11

### Changed

- Correct black/white substitutions on RGB colors

## [0.0.2] - 2018-01-25

### Added

- Add more test cases to get coverage number above 85%

### Changed

- Rewrite style proprety handling to promote items rather than validate in place

## [0.0.1] - 2018-01-05

### Added

- Create the initial simple version
- Create python setup program

[0.5.19]: https://github.com/ietf-tools/rfc2html/compare/0.5.17...0.5.19
[0.5.17]: https://github.com/ietf-tools/rfc2html/compare/0.5.16...0.5.17
[0.5.16]: https://github.com/ietf-tools/rfc2html/compare/0.5.15...0.5.16
[0.5.15]: https://github.com/ietf-tools/rfc2html/compare/0.5.14...0.5.15
[0.5.14]: https://github.com/ietf-tools/rfc2html/compare/0.5.13...0.5.14
[0.5.13]: https://github.com/ietf-tools/rfc2html/compare/0.5.12...0.5.13
[0.5.12]: https://github.com/ietf-tools/rfc2html/compare/0.5.4...0.5.12
[0.5.4]: https://github.com/ietf-tools/rfc2html/compare/0.5.1...0.5.4
[0.5.1]: https://github.com/ietf-tools/rfc2html/compare/0.5.0...0.5.1
[0.5.0]: https://github.com/ietf-tools/rfc2html/compare/0.0.3...0.5.0
[0.0.3]: https://github.com/ietf-tools/rfc2html/compare/0.0.2...0.0.3
[0.0.2]: https://github.com/ietf-tools/rfc2html/compare/0.0.1...0.0.2
[0.0.1]: https://github.com/ietf-tools/rfc2html/releases/tag/0.0.1
