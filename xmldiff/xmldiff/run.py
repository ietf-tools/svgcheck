#!/usr/bin/env python

import optparse
import os
import lxml.etree
import datetime
import six
from rfctools_common.parser import XmlRfc, XmlRfcParser, XmlRfcError
from rfctools_common import log
from DiffNode import DiffRoot, BuildDiffTree, DecorateSourceFile
import string
from xmldiff.zzs2 import EditItem, distance

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
        ll = parser.parse(remove_pis=False).tree
        leftXml = BuildDiffTree(ll)
    except XmlRfcError as e:
        log.exception('Unable to parse the XML document: ' + leftSource, e)
        sys.exit(1)

    rightSource = args[1]
    if not os.path.exists(rightSource):
        sys.exit('No such file: ' + rightSource)

    parser = XmlRfcParser(rightSource, verbose=True,
                          quiet=False, no_network=False)
    try:
        rightXml = parser.parse(remove_pis=False)
        rightXml = BuildDiffTree(rightXml.tree)
    except XmlRfcError as e:
        log.exception('Unable to parse the XML document: ' + rightSource, e)
        sys.exit(1)

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

    templates = {}
    templates_dir = 'Templates'
    templates_dir = os.path.join(os.path.dirname(__file__), 'Templates')
    
    for filename in ['base.html']:
        file = open(os.path.join(templates_dir, filename), 'r')
        templates[filename] = string.Template(file.read())
        file.close

    editSet = distance(leftXml, rightXml, DiffRoot.get_children, DiffRoot.InsertCost,
                       DiffRoot.DeleteCost, DiffRoot.UpdateCost)
    print("edit count = " + str(len(editSet)))
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
        'title': 'XML DIFF FOR FOOBAR',
        'body': ''.join(buffers['body']),
        'leftFile': buffers['leftFile'],
        'rightFile': "<br/>".join(rightLines)
        }
    output = templates['base.html'].substitute(subs)

    filename = options.output_filename
    if not filename:
        filename = basename + ".html"
    if six.PY2:
        file = open(filename, "w")
    else:
        file = open(filename, "w", encoding='utf-8')
    file.write(output)
    file.close()


if __name__ == '__main__':
    main()
