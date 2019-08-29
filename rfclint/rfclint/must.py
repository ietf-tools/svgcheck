# ----------------------------------------------------
# Copyright The IETF Trust 2018-9, All Rights Reserved
# ----------------------------------------------------

import re
import os
import sys
import lxml.etree

from rfclint.CursesCommon import CursesCommon
from rfctools_common import log

if os.name == 'nt':
    import msvcrt

    def get_character():
        return msvcrt.getch()
else:
    import tty
    import termios

    def get_character():
        fd = sys.stdin.fileno()
        oldSettings = termios.tcgetattr(fd)

        try:
            tty.setcbreak(fd)
            answer = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)
            answer = None

        return answer


CutNodes = {
    'annotation': 1,
    'blockquote': 2,
    'dd': 2,
    'dt': 1,
    'li': 2,
    'preamble': 1,
    'refcontent': 1,
    "t": 1,
    'td': 2,
    'th': 2
}


class Lang2119(CursesCommon):
    """ Object to deal with processing spelling and duplicates """
    def __init__(self, config):
        CursesCommon.__init__(self, config)

        self.bcp14_re = re.compile(u"MUST[ |\u00A0]NOT|MUST|REQUIRED|SHALL[ |\u00A0]NOT|SHALL|"
                                   u"SHOULD[ |\u00A0]NOT|SHOULD|"
                                   u"NOT[ |\u00A0]RECOMMENDED|RECOMMENDED|MAY|OPTIONAL", re.UNICODE)

        self.rewrite = False
        if config.options.output_filename is not None:
            self.rewrite = True

    def processTree(self, tree):
        # log.warn("processTree - look at node {0}".format(tree.tag))
        if tree.tag in CutNodes:
            # M00BUG - Should these always be skipped?
            if not ((tree.tag == 'sourcecode' and self.skipCode) or
                    (tree.tag == 'artwork' and self.skipArtwork)):
                self.checkTree(tree)
        for node in tree.iterchildren():
            self.processTree(node)

    def checkTree(self, tree):
        if tree.tag == 'bcp14':
            if not tree.text:
                inner = lxml.etree.tostring(tree, with_tail=False)
                if not isinstance(inner, type('')):
                    inner = inner.decode('utf8')
                log.error(u"text '{0}' in bcp14 tag is not bcp14 language".format(inner),
                          where=tree)
            elif not self.bcp14_re.match(tree.text):
                log.error(u"text '{0}' in bcp14 tag is not bcp14 language".
                          format(tree.text), where=tree)
        elif tree.text:
            xx = self.bcp14_re.search(tree.text)
            if xx:
                if self.rewrite:
                    xx = self.bcp14_re.search(tree.text)
                    bcpNode = lxml.etree.SubElement(tree, "bcp14")
                    bcpNode.text = xx.group(0)
                    bcpNode.tail = tree.text[xx.end(0):]
                    tree.text = tree.text[:xx.start(0)]
                    tree.insert(0, bcpNode)
                else:
                    xx = self.bcp14_re.finditer(tree.text)
                    for x in xx:
                        log.error(u"bcp14 text '{0}' found without bcp14 tag around it".
                                  format(x.group(0)), where=tree)
        if tree.tail:
            xx = self.bcp14_re.search(tree.tail)
            if xx:
                if self.rewrite:
                    parent = tree.getparent()
                    bcpNode = lxml.etree.SubElement(parent, "bcp14")
                    bcpNode.text = xx.group(0)
                    bcpNode.tail = tree.tail[xx.end(0):]
                    tree.tail = tree.tail[:xx.start(0)]
                    parent.insert(parent.index(tree)+1, bcpNode)
                    self.checkTree(bcpNode)
                else:
                    xx = self.bcp14_re.finditer(tree.text)
                    for x in xx:
                        log.error(u"bcp14 text '{0}' found without bcp14 tag around it".
                                  format(x.group(0)), where=tree)

        for node in tree.iterchildren():
            self.checkTree(node)
