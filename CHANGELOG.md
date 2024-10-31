# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.9.0] - 2024-10-31
### :sparkles: New Features
- [`1af4336`](https://github.com/ietf-tools/svgcheck/commit/1af43361b5cb26e2047cb3c7c575ee619f0fb12b) - Add support for Python 3.13 *(PR [#62](https://github.com/ietf-tools/svgcheck/pull/62) by [@kesara](https://github.com/kesara))*
  - :arrow_lower_right: *addresses issue [#58](https://github.com/ietf-tools/svgcheck/issues/58) opened by [@kesara](https://github.com/kesara)*


## [v0.8.1] - 2024-10-14
### :bug: Bug Fixes
- [`40c2914`](https://github.com/ietf-tools/svgcheck/commit/40c2914c688de757b9e72560920dfd890ff0f8f9) - typo heuristic *(PR [#53](https://github.com/ietf-tools/svgcheck/pull/53) by [@Rotzbua](https://github.com/Rotzbua))*
  - :arrow_lower_right: *fixes issue [#40](https://github.com/ietf-tools/svgcheck/issues/40) opened by [@gregbo](https://github.com/gregbo)*
- [`b330dfd`](https://github.com/ietf-tools/svgcheck/commit/b330dfdee391be0d757dcc7f426054fe875002b9) - Use correct log info method *(PR [#57](https://github.com/ietf-tools/svgcheck/pull/57) by [@kesara](https://github.com/kesara))*
- [`87031fd`](https://github.com/ietf-tools/svgcheck/commit/87031fdd73ec64a3b94e3a8a9e0bb928cc6a68ad) - Read from STDIN *(PR [#56](https://github.com/ietf-tools/svgcheck/pull/56) by [@kesara](https://github.com/kesara))*
  - :arrow_lower_right: *fixes issue [#36](https://github.com/ietf-tools/svgcheck/issues/36) opened by [@kesara](https://github.com/kesara)*

### :wrench: Chores
- [`21d3c29`](https://github.com/ietf-tools/svgcheck/commit/21d3c29bb9ed0d288c1f4957c5104560b18f7e00) - Remove Python 2.7 check *(PR [#60](https://github.com/ietf-tools/svgcheck/pull/60) by [@kesara](https://github.com/kesara))*


## [v0.8.0] - 2024-04-04
### :sparkles: New Features
- [`6a6de81`](https://github.com/ietf-tools/svgcheck/commit/6a6de81112b2a2cf2056046d0283b9ee5ba4ed75) - Add support for Python 3.12 *(PR [#43](https://github.com/ietf-tools/svgcheck/pull/43) by [@Rotzbua](https://github.com/Rotzbua))*
- [`e5d1820`](https://github.com/ietf-tools/svgcheck/commit/e5d1820cf7428d0744b201cda8a2a1ef52a03676) - Remove support for Python 3.7 *(PR [#49](https://github.com/ietf-tools/svgcheck/pull/49) by [@kesara](https://github.com/kesara))*
  - :arrow_lower_right: *addresses issue [#44](https://github.com/ietf-tools/svgcheck/issues/44) opened by [@kesara](https://github.com/kesara)*
  - :arrow_lower_right: *addresses issue [#47](https://github.com/ietf-tools/svgcheck/issues/47) opened by [@dwaite](https://github.com/dwaite)*

### :bug: Bug Fixes
- [`db9471f`](https://github.com/ietf-tools/svgcheck/commit/db9471feedbe4484a900bba1a5d160c8346b5be5) - Remove duplicate key *(PR [#45](https://github.com/ietf-tools/svgcheck/pull/45) by [@Rotzbua](https://github.com/Rotzbua))*

### :recycle: Refactors
- [`28240de`](https://github.com/ietf-tools/svgcheck/commit/28240deb91fec21739392e892dde240eabda59f5) - Remove Python 2 specific code *(PR [#46](https://github.com/ietf-tools/svgcheck/pull/46) by [@Rotzbua](https://github.com/Rotzbua))*


## [v0.7.1] - 2023-02-01
### :bug: Bug Fixes
- [`182b486`](https://github.com/ietf-tools/svgcheck/commit/182b486d86cb98561d34bda2050e53a5dba34400) - No op --no-xinclude option *(PR [#35](https://github.com/ietf-tools/svgcheck/pull/35) by [@kesara](https://github.com/kesara))*


## [v0.7.0] - 2023-01-31
### :sparkles: New Features
- [`ac1cc51`](https://github.com/ietf-tools/svgcheck/commit/ac1cc516f29da1495dfa10e4cfed0b7f720363be) - Use xml2rfc *(PR [#28](https://github.com/ietf-tools/svgcheck/pull/28) by [@kesara](https://github.com/kesara))*
- [`8935e20`](https://github.com/ietf-tools/svgcheck/commit/8935e206769cfe158247c935120271190c27d17a) - Add support for Python 3.11 *(PR [#30](https://github.com/ietf-tools/svgcheck/pull/30) by [@kesara](https://github.com/kesara))*
- [`d1076d2`](https://github.com/ietf-tools/svgcheck/commit/d1076d2ec1a4f73e9992f23d942b38730c7f56a2) - Remove command line option --no-xinclude *(PR [#32](https://github.com/ietf-tools/svgcheck/pull/32) by [@kesara](https://github.com/kesara))*

### :recycle: Refactors
- [`57299b5`](https://github.com/ietf-tools/svgcheck/commit/57299b5873f1a61b3288987ab673611d6f7e562c) - Drop dependency on six in log module *(PR [#29](https://github.com/ietf-tools/svgcheck/pull/29) by [@kesara](https://github.com/kesara))*

### :wrench: Chores
- [`5cafacd`](https://github.com/ietf-tools/svgcheck/commit/5cafacdc47df0128199938aee848c941162b9b13) - Move to setup.cfg *(PR [#24](https://github.com/ietf-tools/svgcheck/pull/24) by [@kesara](https://github.com/kesara))*
  - :arrow_lower_right: *addresses issue [#1](undefined) opened by [@dkg](https://github.com/dkg)*
  - :arrow_lower_right: *addresses issue [#6](undefined) opened by [@rjsparks](https://github.com/rjsparks)*


## [v0.6.2] - 2023-01-19
### :bug: Bug Fixes
- [`f07f3ac`](https://github.com/ietf-tools/svgcheck/commit/f07f3aca8f051641f5e50c79a2f9c21a84f4b35b) - remove obsolete text. Fixes [#19](https://github.com/ietf-tools/svgcheck/pull/19). *(commit by [@rjsparks](https://github.com/rjsparks))*


## [v0.6.1] - 2022-04-05
### :white_check_mark: Tests
- [`265b214`](https://github.com/ietf-tools/svgcheck/commit/265b2147961b1adafaded13be8f154bd2354357a) - add tox.ini *(commit by [@NGPixel](https://github.com/NGPixel))*
- [`5e75de3`](https://github.com/ietf-tools/svgcheck/commit/5e75de35d4122a450884dd1f97212bd22f56febb) - fix test entry path *(commit by [@NGPixel](https://github.com/NGPixel))*
- [`689ebe0`](https://github.com/ietf-tools/svgcheck/commit/689ebe07be31edfa5dd4cb164e86cf0526713f81) - add missing pycodestyle *(commit by [@NGPixel](https://github.com/NGPixel))*
- [`91febab`](https://github.com/ietf-tools/svgcheck/commit/91febab5098d70da944233f62590338131ed75f7) - missing pyflakes *(commit by [@NGPixel](https://github.com/NGPixel))*
- [`217f4a7`](https://github.com/ietf-tools/svgcheck/commit/217f4a7e29a8d1df6c735ba78a2d87be3b8c2874) - update Results. address pep8 complaint. *(PR [#3](https://github.com/ietf-tools/svgcheck/pull/3) by [@rjsparks](https://github.com/rjsparks))*

### :wrench: Chores
- [`5da8749`](https://github.com/ietf-tools/svgcheck/commit/5da8749f0505065634d1d1ada9921e86bda6464f) - exclude non-svgcheck files *(commit by [@NGPixel](https://github.com/NGPixel))*


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

[v0.6.1]: https://github.com/ietf-tools/svgcheck/compare/0.6.0...v0.6.1
[v0.6.2]: https://github.com/ietf-tools/svgcheck/compare/v0.6.1...v0.6.2
[v0.7.0]: https://github.com/ietf-tools/svgcheck/compare/v0.6.2...v0.7.0
[v0.7.1]: https://github.com/ietf-tools/svgcheck/compare/v0.7.0...v0.7.1
[v0.8.0]: https://github.com/ietf-tools/svgcheck/compare/v0.7.1...v0.8.0
[v0.8.1]: https://github.com/ietf-tools/svgcheck/compare/v0.8.0...v0.8.1
[v0.9.0]: https://github.com/ietf-tools/svgcheck/compare/v0.8.1...v0.9.0
