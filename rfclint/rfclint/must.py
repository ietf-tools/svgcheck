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

        # [^\W\d_]
        self.word_re = re.compile(r'(\W*\w+\W*)', re.UNICODE | re.MULTILINE)
        self.word_re = re.compile(r'([\W\d_]*[^\W\d_]+[\W\d_]*)', re.UNICODE | re.MULTILINE)
        # self.word_re = re.compile(r'\w+', re.UNICODE | re.MULTILINE)

        # pattern to match output of aspell
        self.aspell_re = re.compile(r".\s(\S+)\s(\d+)\s*((\d+): (.+))?", re.UNICODE)

        self.spell_re = re.compile(r'\w[\w\'\u00B4\u2019]*\w', re.UNICODE)
        self.spell_re = re.compile(r'[^\W\d_]([^\W\d_]|[\'\u00B4\u2019])*[^\W\d_]', re.UNICODE)

        self.bcp14_re = re.compile(r"MUST NOT|MUST|REQUIRED|SHALL NOT|SHALL|SHOULD NOT|SHOULD|"
                                   r"RECOMMENDED NOT|RECOMMENDED|MAY|OPTIONAL")

        if config.options.output_filename is not None:
            self.lastElement = None
            self.textLocation = True

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
                log.error("text '{0}' in bcp14 tag is not bcp14 language".format(inner),
                          where=tree)
            elif not self.bcp14_re.match(tree.text):
                log.error("text '{0}' in bcp14 tag is not bcp14 language".
                          format(tree.text), where=tree)
            return
        if tree.text:
            xx = self.bcp14_re.finditer(tree.text)
            for x in xx:
                log.error("bcp14 text '{0}' found with out bcp14 tag around it".
                          format(x.group(0)), where=tree)
        if tree.tail:
            xx = self.bcp14_re.finditer(tree.tail)
            for x in xx:
                log.error("bcp14 text '{0}' found with out bcp14 tag around it".
                          format(x.group(0)), where=tree)
        for node in tree.iterchildren():
            self.checkTree(node)
