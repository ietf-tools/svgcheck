#!/usr/bin/env python
# ----------------------------------------------------
# Copyright The IETF Trust 2018-9, All Rights Reserved
# ----------------------------------------------------


import optparse
import os
import six
import sys
from rfctools_common.parser import XmlRfcParser, XmlRfcError, CACHES
from rfctools_common.parser import CachingResolver
from rfctools_common import log
from rfctools_common.log import write_to
from xmldiff.DiffNode import DiffRoot, BuildDiffTree, AddParagraphs
from xmldiff.DiffNode import SourceFiles
from rfctools_common.__init__ import __version__ as toolsVersion
import string
from xmldiff.zzs2 import distance
# from xmldiff.zzs import distance, EditItem
from xmldiff.__init__ import __version__

if six.PY2:
    from urlparse import urlparse
else:
    from urllib.parse import urlparse

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
    print("xmldiff = " + __version__)
    print("rfctools_common = " + toolsVersion)
    sys.exit()


def clear_cache(cache_path):
    XmlRfcParser('', cache_path=cache_path).delete_cache()
    sys.exit()


def formatLines(lines, side, fileNumber):
    output = '<div itemprop="text" class="blob-wrapper data type-c">\n'
    output += '<table class="highlight tab-size js-file-line-container" data-tab-size="8">\n'
    output += "<col width='4em'/>\n"

    iLine = 1
    for line in lines:
        output += u'<tr id="{2}{4}_{3}"><td class="blob-num js-line-number" ' \
                  'data-line-number="{0}">{0}</td>' \
                  '<td class="blob-code blob-code-inner js-file-line">{1}</td></tr>\n'. \
                  format(iLine, line, side, fileNumber, iLine-1)
        iLine += 1
    output += "</table>\n</div>\n"

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
                             default=None)
    value_options.add_option('--debug', action="store_true",
                             help='Show debugging output')
    value_options.add_option('--raw', action="store_true",
                             help='Diff using the raw tree')
    value_options.add_option('-t', '--template', dest='template', metavar='FILE',
                             help='specify the HTML template filename',
                             default='base.html')
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
    value_options.add_option('-X', '--no-xinclude', action='store_true', dest='no_xinclude',
                             help='don\'t resolve any xi:include elements')
    value_options.add_option('-D', '--no-defaults', action='store_false', default=True,
                             help="don't add default attributes")

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
                          no_xinclude=options.no_xinclude,
                          resolve_entities=not options.noEntity,
                          attribute_defaults=options.no_defaults)
    try:
        ll = parser.parse(remove_pis=False, strip_cdata=False, remove_comments=False).tree
        leftXml = BuildDiffTree(ll, options)
        if not options.raw:
            leftXml = AddParagraphs(leftXml)
        leftFile_base = os.path.basename(leftSource)
        SourceFiles.LeftDone()
    except XmlRfcError as e:
        log.exception('Unable to parse the XML document: ' + leftSource, e)
        sys.exit(1)

    rightSource = args[1]
    if not os.path.exists(rightSource):
        sys.exit('No such file: ' + rightSource)

    parser = XmlRfcParser(rightSource, verbose=log.verbose,
                          quiet=log.quiet, no_network=options.no_network,
                          no_xinclude=options.no_xinclude,
                          resolve_entities=not options.noEntity,
                          attribute_defaults=options.no_defaults)
    try:
        rightXml = parser.parse(remove_pis=False, strip_cdata=False, remove_comments=False)
        rightXml = BuildDiffTree(rightXml.tree, options)
        if not options.raw:
            rightXml = AddParagraphs(rightXml)
        rightFile_base = os.path.basename(rightSource)
    except XmlRfcError as e:
        log.exception('Unable to parse the XML document: ' + rightSource, e)
        sys.exit(1)

    log.note("Read files for source display")
    cache = CachingResolver(library_dirs=[])

    leftSources = ""
    leftSourceNames = ""
    for i in range(len(SourceFiles.leftFiles)):
        file = SourceFiles.leftFiles[i]
        if file[:5] == 'file:':
            file = urlparse(file)
            file = file[2]
            if file[2] == ':':
                file = file[1:]
        else:
            file = cache.getReferenceRequest(file)[0]

        if six.PY2:
            with open(file, "rb") as f:
                leftLines = f.read()
                leftLines = leftLines.decode('utf8').splitlines(1)
        else:
            with open(file, "rU", encoding="utf8") as f:
                leftLines = f.readlines()

        leftSources += u'<div id="L_File{0}" class="tabcontent">\n'.format(i)
        leftLines = [escape(x).replace(' ', '&nbsp;').replace('"', '&quot;') for x in leftLines]
        leftSources += formatLines(leftLines, 'L', i)
        leftSources += u'</div>\n'

        leftSourceNames += u'<option label="{0}" value="L_File{1}">{2}</option>\n'. \
                           format(file, i, file)

    rightSources = ""
    rightSourceNames = ""

    for i in range(len(SourceFiles.rightFiles)):
        file = SourceFiles.rightFiles[i]
        if file[:5] == 'file:':
            file = urlparse(file)
            file = file[2]
            if file[2] == ':':
                file = file[1:]
        else:
            file = cache.getReferenceRequest(file)[0]

        if six.PY2:
            with open(file, "rb") as f:
                rightLines = f.read().decode('utf8').splitlines(1)
        else:
            with open(file, "rU", encoding="utf8") as f:
                rightLines = f.readlines()

        rightSources += u'<div id="R_File{0}" class="tabcontent">\n'.format(i)
        rightLines = [escape(x).replace(' ', '&nbsp;').replace('"', '&quot;') for x in rightLines]
        rightSources += formatLines(rightLines, 'R', i)
        rightSources += u'</div>\n'

        rightSourceNames += '<option label="{0}" value="R_File{1}">{2}</option>\n'. \
                            format(file, i, file)

    log.note("Start computing tree edit distance")
    editSet = distance(leftXml, rightXml, DiffRoot.get_children, DiffRoot.InsertCost,
                       DiffRoot.DeleteCost, DiffRoot.UpdateCost)

    if options.debug:
        print("edit count = " + str(len(editSet)))
        for edit in editSet:
            print(edit.toString())

    log.note("Apply copmuted tree edits")
    if len(editSet) == 0:
        log.info("Files are identical")

    leftXml.applyEdits(editSet)

    log.note("Setup to write html file")
    templates_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'Templates')
    log.note("   template directory = " + templates_dir)

    if six.PY2:
        with open(os.path.join(templates_dir, "resize.js"), "rb") as f:
            allScript = f.read()
    else:
        with open(os.path.join(templates_dir, "resize.js"), "rU", encoding="utf8") as f:
            allScript = f.read()

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
    buffers['leftFile'] = leftSources
    buffers['rightFile'] = rightSources
    buffers['body'] = leftXml.ToString()

    subs = {
        'background': '',
        # HTML-escaped values
        'title': 'rfc-xmldiff {0} {1}'.format(leftFile_base, rightFile_base),
        'body': ''.join(buffers['body']),
        'leftFile': buffers['leftFile'],
        'leftSourceNames': leftSourceNames,
        'rightFile': buffers['rightFile'],
        'rightSourceNames': rightSourceNames,
        'allScript': allScript
        }
    output = html_template.substitute(subs)

    if options.output_filename is None:
        write_to(sys.stdout, output)
    else:
        log.note('Write out html file: ' + options.output_filename)
        file = open(options.output_filename, "wb")
        file.write(output.encode('utf8'))
        file.close()


if __name__ == '__main__':
    main()
