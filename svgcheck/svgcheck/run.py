import sys
import optparse
import os
import lxml.etree
from svgcheck.checksvg import checkTree, errorCount
from rfctools_common import log
from rfctools_common.parser import XmlRfc, XmlRfcParser, XmlRfcError, CACHES

__version__ = '0.0.1'


def display_version(self, opt, value, parser):
    print(svgcheck.__version__)
    sys.exit()


def clear_cache(self, opt, value, parser):
    XmlRfcParser('').delete_cache()
    sys.exit()


def main():
    # Populate the options
    formatter = optparse.IndentedHelpFormatter(max_help_position=40)
    optionparser = optparse.OptionParser(usage='svgcheck SOURCE [OPTIONS] '
                                         '...\nExample: svgcheck draft.xml',
                                         formatter=formatter)

    parser_options = optparse.OptionGroup(optionparser, 'Parser Optoins')
    parser_options.add_option('-C', '--clear-cache', action='callback', callback=clear_cache,
                              help='purge the cache and exit')
    parser_options.add_option('-N', '--no-network', action='store_true', default=False,
                              help='don\'t use the network to resolve references')
    parser_options.add_option('-c', '--cache', dest='cache',
                              help='specify a primary cache directory to write to;'
                              'default: try [ %s ]' % ', '.join(CACHES))
    parser_options.add_option('-d', '--rng', dest='rng', help='specify an alternate RNG file')
    optionparser.add_option_group(parser_options)

    other_options = optparse.OptionGroup(optionparser, 'Other options')
    other_options.add_option('-q', '--quiet', action='store_true',
                             help='don\'t print anything')
    other_options.add_option('-o', '--out', dest='output_filename', metavar='FILE',
                             help='specify an explicit output filename')
    other_options.add_option('-v', '--verbose', action='store_true',
                             help='print extra information')
    other_options.add_option('-V', '--version', action='callback', callback=display_version,
                             help='display the version number and exit')
    optionparser.add_option_group(other_options)

    svg_options = optparse.OptionGroup(optionparser, 'SVG options')
    svg_options.add_option('-r', '-repair', action='store_true', default=False,
                           help='Repair the SVG so it meets RFC 7966')
    optionparser.add_option_group(svg_options)

    # --- Parse and validate arguments --------------

    (options, args) = optionparser.parse_args()

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

    if options.cache:
        if not os.path.exists(options.cache):
            try:
                os.makedirs(options.cache)
                if options.verbose:
                    log.write('Created cache directory at',
                              options.cache)
            except OSError as e:
                print('Unable to make cache directory: %s ' % options.cache)
                print(e)
                sys.exit(1)
        else:
            if not os.access(options.cache, os.W_OK):
                print('Cache directory is not writable: %s' % options.cache)
                sys.exit(1)

    # Setup warnings module
    # rfclint.log.warn_error = options.warn_error and True or False
    log.quiet = options.quiet and True or False
    log.verbose = options.verbose

    # Parse the document into an xmlrfc tree instance
    parser = XmlRfcParser(source, verbose=options.verbose,
                          quiet=options.quiet,
                          cache_path=options.cache,
                          no_network=options.no_network)
    try:
        xmlrfc = parser.parse(remove_pis=True)
    except XmlRfcError as e:
        log.exception('Unable to parse the XML document: ' + source, e)
        sys.exit(1)
    except lxml.etree.XMLSyntaxError as e:
        # Give the lxml.etree.XmlSyntaxError exception a line attribute which
        # matches lxml.etree._LogEntry, so we can use the same logging function
        log.exception('Unable to parse the XML document: ' + source, e.error_log)
        sys.exit(1)

    # Check that

    if not checkTree(lxml.getroot()):
        if options.repair:
            if options.output_filename is None:
                options.output_filename = source + '.new'
            file = open(options.output_filename, 'w', encoding='utf8')
            fle.write(lxml.etree.tostring(xmlrfc.tree.getroot(), pretty_print=True))
        else:
            sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    major, minor = sys.version_info[:2]
    if major == 2 and minor < 7:
        print("")
        print("The svgcheck script requires python of 2.7 or higher.")
        print("Can't proceed, quitting.")
        exit()

    main()
