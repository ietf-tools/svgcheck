#!/usr/bin/env python

from __future__ import print_function

import sys

import re
import optparse
import os
import lxml.etree
import six
from rfctools_common.parser import XmlRfcParser, XmlRfcError, CACHES, CachingResolver
from rfctools_common import log
from rfclint.config import ConfigFile
from rfclint.abnf import AbnfChecker, RfcLintError
from rfclint.spell import Speller, SpellerColors
from rfclint.dups import Dups
from svgcheck.checksvg import checkTree
import rfclint

try:
    import debug
    assert debug
except ImportError:
    pass


def display_version(self, opt, value, parser):
    print(rfclint.__version__)
    sys.exit()


def clear_cache(cache_path):
    XmlRfcParser('', cache_path=cache_path).delete_cache()
    sys.exit()


def check_color(option, opt, value, parser):
    if value not in SpellerColors:
        raise optparse.OptionValueError("color value not supported. Use one of '{0}'".
                                        format(" ".join(SpellerColors.keys())))
    setattr(parser.values, option.dest, value)


def main():
    # Populate options
    formatter = optparse.IndentedHelpFormatter(max_help_position=40)
    optionparser = optparse.OptionParser(usage='rfclint SOURCE [OPTIONS] '
                                         '...\nExample: rfclint '
                                         'draft.xml',
                                         formatter=formatter)

    parser_options = optparse.OptionGroup(optionparser, "Parser Options")
    parser_options.add_option('-C', '--clear-cache', action='store_true', dest='clear_cache',
                              default=False, help='purge the cache and exit')
    parser_options.add_option('-c', '--cache', dest='cache',
                              help='specify a primary cache directory to'
                              ' write to; default: try [ %s ]' % ', '.join(CACHES))
    parser_options.add_option('-N', '--no-network', action='store_true', default=False,
                              help='don\'t use the network to resolve references')
    parser_options.add_option('-n', '--no-rng', action='store_true',
                              help='disable RNG validation step')
    parser_options.add_option('-r', '--rng', action='store_true',
                              help='Specify an alternate RNG file')
    parser_options.add_option('-X', '--no-xinclude', action='store_true', dest='no_xinclude',
                              help='don\'t resolve any xi:include elements')
    parser_options.add_option('--no-xml', dest='no_xml', action='store_true',
                              help='Don\'t perform XML well-formness checking')

    optionparser.add_option_group(parser_options)

    general_options = optparse.OptionGroup(optionparser, "General Options")
    general_options.add_option('-o', '--out', dest='output_filename', metavar='FILE',
                               help='specify an explicit output filename')
    optionparser.add_option_group(general_options)

    plain_options = optparse.OptionGroup(optionparser, 'Plain Options')

    plain_options.add_option('-q', '--quiet', action='store_true',
                             help='dont print anything')
    plain_options.add_option('-v', '--verbose', action='store_true',
                             help='print extra information')
    plain_options.add_option('-V', '--version', action='callback', callback=display_version,
                             help='display the version number and exit')
    plain_options.add_option('--debug', action='store_true',
                             help='Show debugging output')
    plain_options.add_option('--extract', dest='extract',
                             help='Extract all items of the given type')
    plain_options.add_option('--no-svgcheck', action='store_true', dest='no_svgcheck',
                             help='Don\'t run svgcheck')
    optionparser.add_option_group(plain_options)

    spell_options = optparse.OptionGroup(optionparser, 'Spell Options')
    spell_options.add_option('--no-spell', dest='no_spell', default=False, action='store_true',
                             help='Don\'t run the spell checking')
    spell_options.add_option('--dictionary', dest='dict_list', action='append',
                             help='Use this addition dictionary when spell checking')
    spell_options.add_option('--personal', dest='dict_personal',
                             help='use this dictionary as the personal dictionary')
    spell_options.add_option('--spell-window', dest='spell_window', action='store',
                             type='int',
                             help='Set the number of words to appear around spelling errors')
    spell_options.add_option('--no-dup-detection', dest='no_dups', action='store_true',
                             help='Don\'t do duplication detection.')
    spell_options.add_option('--spell-program', dest='spell_program', metavar='NAME',
                             help='Name of spelling program to use')
    spell_options.add_option('--no-suggest', dest='spell_suggest', action='store_false',
                             help='Do not provide suggestions')
    spell_options.add_option('--suggest', dest='spell_suggest', action='store_true',
                             help='provide suggestions (default)')
    spell_options.add_option('--color', dest='spell_color', action='callback',
                             callback=check_color, type='string',
                             help='color incorrect words in supplied context')
    spell_options.add_option('--no-curses', dest='no_curses', action='store_true',
                             help='disable curses when doing spell checking and dup detection')
    spell_options.add_option('--skip-code', dest='skip_code', action='store_true',
                             help='skip all code elements when doing spell and duplicate checking')
    spell_options.add_option('--skip-artwork', dest='skip_artwork', action='store_true',
                             help='skip all artwork elements when doing spell and '
                             'duplicate checking')
    optionparser.add_option_group(spell_options)

    abnf_options = optparse.OptionGroup(optionparser, 'ABNF Options')
    abnf_options.add_option('--abnf-program', dest='abnf_program', metavar='NAME',
                            help='Name of ABNF checker program to use')
    abnf_options.add_option('--no-abnf', dest='no_abnf', action='store_true',
                            help='Don\'t perform ABNF checking')
    abnf_options.add_option('--abnf-add-rules', dest='abnf_add',
                            help='ABNF file to append during evaluation.')

    config_options = optparse.OptionGroup(optionparser, 'Configuration Options')
    config_options.add_option('--configfile', dest='config_file', metavar='NAME',
                              help="Specify the name of the configuration file.")
    config_options.add_option('--save-config', dest='save_config', default=False,
                              action='store_true', help='Save configuration back to file')

    # --- Parse and validate arguments ---------------------------------

    (options, args) = optionparser.parse_args()

    # --- Setup and parse the input file

    if options.cache:
        if not os.path.exists(options.cache):
            try:
                os.makedirs(options.cache)
                if options.verbose:
                    log.write('Created cache directory at', options.cache)
            except OSError as e:
                print('Unable to make cache directory: %s ' % options.cache)
                print(e)
                sys.exit(1)
        else:
            if not os.access(options.cache, os.W_OK):
                print('Cache directory is not writable: %s' % options.cache)
                sys.exit(1)

    if options.clear_cache:
        clear_cache(options.cache)

    # --- Locate the configuration file if it exists and import it ----

    config = ConfigFile(options)

    if options.save_config:
        config.save()
        sys.exit(0)

    # make things quiet if output goes to stdout
    if options.output_filename is None and not options.quiet and (
            options.extract):
        options.quiet = True

    # --- Get the file to be processed --------------------------------

    if len(args) < 1:
        optionparser.print_help()
        sys.exit(2)
    source = args[0]
    if not os.path.exists(source):
        sys.exit('No such file: ' + source)

    # Setup warnings module
    # rfclint.log.warn_error = options.warn_error and True or False
    log.quiet = options.quiet and True or False
    log.verbose = options.verbose

    # Parse the document into an xmlrfc tree instance
    log.note("Checking for well-formness of '{0}'".format(source))
    parser = XmlRfcParser(source, verbose=options.verbose,
                          preserve_all_white=True,
                          quiet=True,
                          cache_path=options.cache,
                          no_network=options.no_network,
                          no_xinclude=options.no_xinclude,
                          templates_path=globals().get('_TEMPLATESPATH', None))
    try:
        xmlrfc = parser.parse(remove_comments=False,
                              strip_cdata=False)
    except XmlRfcError as e:
        log.exception('Unable to parse the XML document: ' + source, e)
        sys.exit(1)
    except lxml.etree.XMLSyntaxError as e:
        # Give the lxml.etree.XmlSyntaxError exception a line attribute which
        # matches lxml.etree._LogEntry, so we can use the same logging function
        log.error("Unable to parse the XML document: " + os.path.normpath(source))
        log.exception_lines("dummy", e.error_log)
        sys.exit(1)
    log.note("Well-formness passes")

    # Validate the document unless disabled
    if not options.no_rng:
        log.note("Checking for schema validation...")
        if not options.rng:
            options.rng = parser.default_rng_path
        ok, errors = xmlrfc.validate(rng_path=options.rng)
        if not ok:
            log.error('Unable to validate the XML document: ' + os.path.normpath(source))
            log.exception_lines("dummy", errors)
            sys.exit(1)
        log.info("Schema validation passes")
    else:
        log.note("Skipping schema validation")

    # Do Extracts

    if options.extract:
        codeItems = xmlrfc.tree.getroot().xpath("//sourcecode[@type='{0}']".format(options.extract))

        if len(codeItems) == 0:
            log.error("No sourcecode elements with type = '{0}' found.".format(options.extract))
            exit(1)

        if options.output_filename:
            file = open(options.output_filename, 'w')
        else:
            file = sys.stdout

        needEOL = True
        for item in codeItems:
            if "name" in item.attrib:
                with open(item.attrib["name"], 'w') as f:
                    f.write(item.text)
                    if len(item.text) > 0 and item.text[-1] != '\n':
                        f.write('\n')
            else:
                file.write(item.text)
                if len(item.text) > 0:
                    needEOL = item.text[-1] != '\n'

        if needEOL:
            file.write('\n')

        if options.output_filename:
            file.close()
        exit(0)

    #  Validate any embedded XML

    if not options.no_xml:
        codeItems = xmlrfc.tree.getroot().xpath("//sourcecode[@type='xml']")
        if len(codeItems) > 0:
            log.note("Validating XML fragments in sourcecode elements")
            # resolver without knowledge of rfc_number:
            caching_resolver = CachingResolver(no_network=True,
                                               verbose=options.verbose,
                                               quiet=options.quiet)

            for item in codeItems:
                parser = lxml.etree.XMLParser(dtd_validation=False, load_dtd=False, no_network=True,
                                              resolve_entities=False, recover=False)
                parser.resolvers.add(caching_resolver)
                try:
                    text = re.sub(u'^\s+<\?xml ', '<?xml ', item.text)
                    file = six.BytesIO(text.encode('utf-8'))

                    lxml.etree.parse(file, parser)
                    log.info("XML fragment in source code found and is well defined.", where=item)
                except (lxml.etree.XMLSyntaxError) as e:
                    log.warn(u'XML in sourcecode not well formed: ', e.msg, where=item)
                except Exception as e:
                    log.exception(u'Error occured processing XML: ', e)
        else:
            log.info("No XML fragments in sourcecode elements found.")

    #  Validate any embedded ABNF
    if not options.no_abnf:
        try:
            checker = AbnfChecker(config)

            checker.validate(xmlrfc.tree)
        except RfcLintError as e:
            log.error("Skipping ABNF checking because")
            log.error(e.message, additional=2)

    # Validate any SVG items
    if not options.no_svgcheck:
        checkTree(xmlrfc.tree)

    # do the Spelling checking
    if not options.no_spell:
        speller = None
        try:
            speller = Speller(config)
            if options.no_curses:
                speller.no_curses = True
            speller.initscr()
            speller.processTree(xmlrfc.tree.getroot())
            speller.sendCommand("#")  # save personal dictionary
            speller.endwin()
        except RfcLintError as e:
            log.error("Skipping spell checking because")
            log.error(e.message, additional=2)
            if speller:
                speller.endwin()
        except Exception:
            if speller:
                speller.endwin()
            raise

    # do the Duplicate checking
    if not options.no_dups:
        try:
            dups = Dups(config)
            if options.no_curses:
                dups.no_curses = True
            dups.initscr()
            dups.processTree(xmlrfc.tree.getroot())
            dups.endwin()
        except RfcLintError as e:
            dups.endwin()
            log.error("Skipping duplicate checking because")
            log.error(e.message, additional=2)
        except Exception:
            dups.endwin()
            raise

    if options.output_filename is not None:
        if six.PY2:
            file = open(options.output_filename, 'w')
        else:
            file = open(options.output_filename, 'w', encoding='utf8')
        text = lxml.etree.tostring(xmlrfc.tree.getroot(),
                                   xml_declaration=True,
                                   encoding='utf-8',
                                   doctype=xmlrfc.tree.docinfo.doctype)
        if six.PY3:
            text = text.decode('utf8')
        file.write(text)
        if len(text) > 0 and text[-1] != '\n':
            file.write('\n')


if __name__ == '__main__':
    major, minor = sys.version_info[:2]
    if major == 2 and minor < 7:
        print("")
        print("The rfclint script requires python 2, with a version of 2.7 or higher.")
        print("Can't proceed, quitting.")
        exit()

    main()
