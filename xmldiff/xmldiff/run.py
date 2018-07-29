#!/usr/bin/env python

import optparse
import os
import lxml.etree
import datetime
import six
import sys
from rfctools_common.parser import XmlRfc, XmlRfcParser, XmlRfcError, CACHES
from rfctools_common import log
from xmldiff.DiffNode import DiffRoot, BuildDiffTree, DecorateSourceFile, AddParagraphs, tagMatching
import string
from xmldiff.EditItem import EditItem
from xmldiff.zzs2 import distance
# from xmldiff.zzs import distance, EditItem
from xmldiff.__init__ import __version__

try:
    import debug
    assert debug
except ImportError:
    pass

try:
    from html import escape  # python 3.x
except ImportError:
    from cgi import escape   # pthyon 2.x


def display_version(self, opt, value, parser):
    print(__version__)
    sys.exit()


def clear_cache(cache_path):
    XmlRfcParser('', cache_path=cache_path).delete_cache()
    sys.exit()


def formatLines(lines, side):
    output = '<div itemprop="text" class="blob-wrapper data type-c">'
    output += '<table class="highlight tab-size js-file-line-container" data-tab-size="8">'
    output += "<col width='4em'>"

    iLine = 1
    for line in lines:
        output += '<tr id="{2}{4}_{3}"><td class="blob-num js-line-number" ' \
                  'data-line-number="{0}">{0}</td>' \
                  '<td class="blob-code blob-code-inner js-file-line">{1}</td></tr>'. \
                  format(iLine, line, side, '0', iLine-1)
        iLine += 1
    output += "</table></div>"

    return output


def main():
    """ Main function for xmldiff """

    formatter = optparse.IndentedHelpFormatter(max_help_position=40)
    optionparser = optparse.OptionParser(usage='xmldiff LEFT RIGHT [OPTIONS] '
                                         '...\nExample: rfc-xmldiff '
                                         'draft1.xml draft2.xml',
                                         formatter=formatter)

    value_options = optparse.OptionGroup(optionparser, 'Other Options')
    value_options.add_option('-o', '--out', dest='output_filename', metavar='FILE',
                             help='specify an explicit output filename',
                             default="xmldiff.html")
    value_options.add_option('--debug', action="store_true",
                             help='Show debugging output')
    value_options.add_option('--raw', action="store_true",
                             help='Diff using the raw tree')
    value_options.add_option('-t', '--template', dest='template', metavar='FILE',
                             help='specify the HTML template filename',
                             default='single.html')
    value_options.add_option('--resource-url', dest='resource_url',
                             help='Path to resources in the template')
    value_options.add_option('-V', '--version', action='callback', callback=display_version,
                             help='display the version number and exit')
    value_options.add_option('-C', '--clear-cache', action='store_true', dest='clear_cache',
                             default=False, help='purge the cache and exit')
    value_options.add_option('-c', '--cache', dest='cache',
                             help='specify a primary cache directory to write to; '
                             'default: try [ %s ]' % ', '.join(CACHES))
    value_options.add_option('-q', '--quiet', action='store_true',
                             help='dont print anything')
    value_options.add_option('-v', '--verbose', action='store_true',
                             help='print extra information')
    value_options.add_option('--no-resolve-entities', dest='noEntity',
                             action="store_true",
                             help="Don't resolve entities in the XML")
    value_options.add_option('-N', '--no-network', action='store_true', default=False,
                             help='don\'t use the network to resolve references')

    optionparser.add_option_group(value_options)

    # --- Parse and validate arguments ----------------------------

    (options, args) = optionparser.parse_args()

    if options.clear_cache:
        clear_cache(options.cache)

    if len(args) < 1:
        optionparser.print_help()
        sys.exit(2)

    # Setup warnings module
    # rfclint.log.warn_error = options.warn_error and True or False
    log.quiet = options.quiet and True or False
    log.verbose = options.verbose

    # Load the left file
    leftSource = args[0]
    if not os.path.exists(leftSource):
        sys.exit('No such file: ' + leftSource)

    log.note("Parse input files")
    parser = XmlRfcParser(leftSource, verbose=log.verbose,
                          quiet=log.quiet, no_network=options.no_network,
                          resolve_entities=not options.noEntity)
    try:
        ll = parser.parse(remove_pis=False, strip_cdata=False, remove_comments=False).tree
        leftXml = BuildDiffTree(ll, options)
        if not options.raw:
            leftXml = AddParagraphs(leftXml)
        leftFile_base = os.path.basename(leftSource)
    except XmlRfcError as e:
        log.exception('Unable to parse the XML document: ' + leftSource, e)
        sys.exit(1)

    rightSource = args[1]
    if not os.path.exists(rightSource):
        sys.exit('No such file: ' + rightSource)

    parser = XmlRfcParser(rightSource, verbose=log.verbose,
                          quiet=log.quiet, no_network=options.no_network,
                          resolve_entities=not options.noEntity)
    try:
        rightXml = parser.parse(remove_pis=False, strip_cdata=False, remove_comments=False)
        rightXml = BuildDiffTree(rightXml.tree, options)
        if not options.raw:
            rightXml = AddParagraphs(rightXml)
        rightFile_base = os.path.basename(rightSource)
    except XmlRfcError as e:
        log.exception('Unable to parse the XML document: ' + rightSource, e)
        sys.exit(1)

    if options.raw:
        tagMatching = None

    log.note("Read files for source display")
    if six.PY2:
        with open(leftSource, "rU") as f:
            leftLines = f.readlines()
    else:
        with open(leftSource, "rU", encoding="utf8") as f:
            leftLines = f.readlines()

    leftLines = [escape(x).replace(' ', '&nbsp;') for x in leftLines]

    if six.PY2:
        with open(rightSource, "rU") as f:
            rightLines = f.readlines()
    else:
        with open(rightSource, "rU", encoding="utf8") as f:
            rightLines = f.readlines()

    rightLines = [escape(x).replace(' ', '&nbsp;') for x in rightLines]

    log.note("Start computing tree edit distance")
    editSet = distance(leftXml, rightXml, DiffRoot.get_children, DiffRoot.InsertCost,
                       DiffRoot.DeleteCost, DiffRoot.UpdateCost)

    if options.debug:
        print("edit count = " + str(len(editSet)))
        for edit in editSet:
            print(edit.toString())

    log.note("Apply copmuted tree edits")
    leftXml.applyEdits(editSet)

    log.note("Setup to write html file")
    templates_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'Templates')
    log.note("   template directory = " + templates_dir)

    if options.resource_url is None:
        options.resource_url = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'Templates')
        if os.name == 'nt':
            options.resource_url = 'file:///' + options.resource_url.replace('\\', '/')
        else:
            options.resource_url = 'file://' + options.resource_url
        # options.resource_url = 'https://www.augustcellars.com/RfcEditor'

    log.note("   resource url: " + options.resource_url)

    template_file = options.template
    if not os.path.exists(options.template):
        template_file = os.path.join(templates_dir, options.template)
        if not os.path.exists(template_file):
            sys.exit('No template file: ' + template_file)

    log.note('   template source file: ' + template_file)
    with open(template_file, 'rb') as file:
        html_template = string.Template(file.read().decode('utf8'))

    rightLines = [x.replace(' ', '&nbsp;') for x in rightLines]

    buffers = {}
    buffers['leftFile'] = formatLines(leftLines, 'L')
    buffers['rightFile'] = formatLines(rightLines, 'R')
    buffers['body'] = leftXml.ToString()

    subs = {
        'background': '',
        # HTML-escaped values
        'title': 'rfc-xmldiff {0} {1}'.format(leftFile_base, rightFile_base),
        'body': ''.join(buffers['body']),
        'leftFile': buffers['leftFile'],
        'rightFile': buffers['rightFile'],
        'resource_dir': options.resource_url
        }
    output = html_template.substitute(subs)

    log.note('Write out html file: ' + options.output_filename)
    file = open(options.output_filename, "wb")
    file.write(output.encode('utf8'))
    file.close()


if __name__ == '__main__':
    main()
