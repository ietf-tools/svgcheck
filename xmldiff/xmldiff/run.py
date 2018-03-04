#!/usr/bin/env python

import optparse
import os
import lxml.etree
import datetime
import six
import sys
from rfctools_common.parser import XmlRfc, XmlRfcParser, XmlRfcError
from rfctools_common import log
from xmldiff.DiffNode import DiffRoot, BuildDiffTree, DecorateSourceFile, AddParagraphs, tagMatching
import string
from xmldiff.EditItem import EditItem
from xmldiff.zzs2 import distance
# from xmldiff.zzs import distance, EditItem

try:
    import debug
    assert debug
except ImportError:
    pass

try:
    from html import escape  # python 3.x
except ImportError:
    from cgi import escape   # pthyon 2.x


def formatLines(lines):
    output = '<div itemprop="text" class="blob-wrapper data type-c">'
    output += '<table class="highlight tab-size js-file-line-container" data-tab-size="8">'
    output += "<col width='4em'>"

    iLine = 1
    for line in lines:
        output += '<tr><td class="blob-num js-line-number" data-line-number="{0}">{0}</td>' \
                  '<td class="blob-code blob-code-inner js-file-line">{1}</td></tr>'. \
                  format(iLine, line)
        iLine += 1
    output += "</table></div>"

    return output


def main():
    """ Main function for xmldiff """

    formatter = optparse.IndentedHelpFormatter(max_help_position=40)
    optionparser = optparse.OptionParser(usage='xmldiff LEFT RIGHT [OPTIONS] '
                                         '...\nExample: rfclint '
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

    # --- Parse and validate arguments ----------------------------

    (options, args) = optionparser.parse_args()

    if len(args) < 2:
        optionparser.print_help()
        sys.exit(2)

    # Load the left file
    leftSource = args[0]
    if not os.path.exists(leftSource):
        sys.exit('No such file: ' + leftSource)

    parser = XmlRfcParser(leftSource, verbose=True,
                          quiet=False, no_network=False)
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

    parser = XmlRfcParser(rightSource, verbose=True,
                          quiet=False, no_network=False)
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

    templates_dir = os.path.join(os.path.dirname(__file__), 'Templates')

    template_file = options.template
    if not os.path.exists(options.template):
        template_file = os.path.join(templates_dir, options.template)
        if not os.path.exists(template_file):
            sys.exit('No template file: ' + options.template)

    with open(template_file, 'rb') as file:
        html_template = string.Template(file.read().decode('utf8'))

    editSet = distance(leftXml, rightXml, DiffRoot.get_children, DiffRoot.InsertCost,
                       DiffRoot.DeleteCost, DiffRoot.UpdateCost)

    if options.debug:
        print("edit count = " + str(len(editSet)))
        for edit in editSet:
            print(edit.toString())

    if options.resource_url is None:
        options.resource_url = os.path.join(os.path.dirname(__file__), 'Templates')
        if os.name == 'nt':
            options.resource_url = 'file:///' + options.resource_url.replace('\\', '/')
        else:
            options.resource_url = 'file://' + options.resource_url

    leftXml.applyEdits(editSet)

    #  DecorateSourceFile(leftXml, leftLines)

    rightLines = [x.replace(' ', '&nbsp;') for x in rightLines]

    buffers = {}
    buffers['leftFile'] = formatLines(leftLines)
    buffers['rightFile'] = "<br/>".join(rightLines)
    buffers['body'] = leftXml.ToString()

    subs = {
        'background': '',
        # HTML-escaped values
        'title': 'rfc-xmldiff {0} {1}'.format(leftFile_base, rightFile_base),
        'body': ''.join(buffers['body']),
        'leftFile': buffers['leftFile'],
        'rightFile': "<br/>".join(rightLines),
        'resource_dir': options.resource_url
        }
    output = html_template.substitute(subs)

    file = open(options.output_filename, "wb")
    file.write(output.encode('utf8'))
    file.close()


if __name__ == '__main__':
    main()
