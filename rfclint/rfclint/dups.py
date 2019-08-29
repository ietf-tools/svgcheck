# ----------------------------------------------------
# Copyright The IETF Trust 2018-9, All Rights Reserved
# ----------------------------------------------------

import re
import os
import sys
import six
try:
    import curses
    haveCurses = True
except ImportError:
    haveCurses = False

from rfclint.CursesCommon import CursesCommon
from rfctools_common import log
from rfclint.spell import RfcLintError, CheckAttributes, CutNodes

if six.PY2:
    from six.moves import input


class Dups(CursesCommon):
    """ Object to deal with processing duplicates """
    def __init__(self, config):
        CursesCommon.__init__(self, config)
        self.word_re = re.compile(r'(\W*\w+\W*)', re.UNICODE | re.MULTILINE)
        # self.word_re = re.compile(r'\w+', re.UNICODE | re.MULTILINE)
        self.aspell_re = re.compile(r".\s(\S+)\s(\d+)\s*((\d+): (.+))?", re.UNICODE)

        self.dupword_re = re.compile(r'\W*([\w\']+)\W*', re.UNICODE)

        self.dup_re = re.compile(r' *\w[\w\']*\w|\w', re.UNICODE)

        if config.options.output_filename is not None:
            self.lastElement = None
            self.textLocation = True

    def processTree(self, tree):
        # log.warn("processTree - look at node {0}".format(tree.tag))
        if tree.tag in CheckAttributes:
            self.checkAttributes(tree)
        if tree.tag in CutNodes:
            if not ((tree.tag == 'sourcecode' and self.skipCode) or
                    (tree.tag == 'artwork' and self.skipArtwork)):
                self.checkTree(tree)
        for node in tree.iterchildren():
            self.processTree(node)

    def checkAttributes(self, tree):
        for attr in CheckAttributes[tree.tag]:
            if attr not in tree.attrib:
                continue
            words = [(tree.attrib[attr], tree, attr, 0)]
            results = self.processLine(words)
            self.processResults(words, results, attr)

    def checkTree(self, tree):
        wordSet = self.getWords(tree)
        results = self.processLine(wordSet)

        self.processResults(wordSet, results, None)

    def processLine(self, allWords):
        """
        """
        result = []
        setNo = 0
        for wordSet in allWords:
            for m in re.finditer(r'\w[\w\']*\w|\w', wordSet[0], re.UNICODE):
                tuple = (m.start(), m.group(0), wordSet[1], setNo)
                result.append(tuple)
            setNo += 1

        return result

    def getWords(self, tree):
        words = []
        if tree.text:
            words += [(tree.text, tree, True, -1)]
        elif tree.tag == 'eref' or tree.tag == 'relref' or tree.tag == 'xref':
            words += [('<' + tree.tag + '>', None, False, -1)]

        for node in tree.iterchildren():
            if node.tag in CutNodes:
                continue
            words += self.getWords(node)

            if node.tail:
                words += [(node.tail, node, False, -1)]

        return words

    def processResults(self, wordSet, results, attributeName):
        """  Process the results coming from a spell check operation """

        matchGroups = []
        for words in wordSet:
            xx = self.word_re.finditer(words[0])
            for w in xx:
                if w:
                    matchGroups.append((w, words[1]))

        # check for dups
        last = None
        lastX = None
        for words in wordSet:
            if words[1] is None:
                last = None
                continue
            xx = self.dup_re.finditer(words[0])
            for w in xx:
                g = w.group(0).strip().lower()
                if last:
                    # print("compare '{0}' and '{1}'".format(last, g))
                    if last == g:
                        if self.interactive:
                            self.Interact(words[1], w, -1, wordSet, words)
                        else:
                            if attributeName:
                                log.error("Duplicate word found '{0}' in attribute '{1}'".
                                          format(lastX, attributeName), where=words[1])
                            else:
                                log.error("Duplicate word found '{0}'".format(lastX),
                                          where=words[1])

                last = g
                lastX = w.group(0).strip()

    def Interact(self, element, match, srcLine, wordSet, words):
        if self.curses:
            self.curses.erase()

            self.curses.move(0, 0)

        fileName = element.base
        if fileName.startswith("file:///"):
            fileName = os.path.relpath(fileName[8:])
        elif fileName[0:6] == 'file:/':
            fileName = os.path.relpath(fileName[6:])
        elif fileName[0:7] == 'http://' or fileName[0:8] == 'https://':
            pass
        else:
            fileName = os.path.relpath(fileName)

        y = 0
        self.x = 0
        self.y = 0

        if isinstance(words[2], str):
            str1 = u"{1}:{2} Duplicate word '{0}' found in attribute '{3}'". \
                   format(match.group(0), fileName, element.sourceline, words[2])
        else:
            str1 = u"{1}:{2} Duplicate word found '{0}'". \
                   format(match.group(0), fileName, element.sourceline)

        if self.curses:
            self.curses.addstr(curses.LINES-14, 0, str1.encode('ascii', 'replaceWithONE'))
        else:
            log.write("")
            log.error(str1)

        self.writeStringInit()
        for line in wordSet:
            if isinstance(line[2], str):
                text = line[1].attrib[line[2]]
            elif line[1] is None:
                text = line[0]
            elif line[2]:
                text = line[1].text
            else:
                text = line[1].tail
            if words == line:
                if self.lastElement != line[1] or self.textLocation != line[2]:
                    self.offset = 0
                    self.lastElement = line[1]
                    self.textLocation = line[2]
                self.writeString(text[:match.start()+self.offset], partialString=True)
                self.writeString(text[match.start()+self.offset:match.end()+self.offset],
                                 self.A_REVERSE, True)
                self.writeString(text[match.end()+self.offset:])
            else:
                self.writeString(text)
            y += 1
        self.writeStringEnd()

        if self.curses:
            self.curses.addstr(curses.LINES-15, 0, self.spaceline, self.A_REVERSE)
            self.curses.addstr(curses.LINES-13, 0, self.spaceline, self.A_REVERSE)

            self.curses.addstr(curses.LINES-2, 0, self.spaceline, self.A_REVERSE)
            self.curses.addstr(curses.LINES-1, 0, "?")

            self.curses.addstr(curses.LINES-11, 0, " ) Ignore")
            self.curses.addstr(curses.LINES-10, 0, "D) Delete Word")
            self.curses.addstr(curses.LINES-9, 0, "R) Replace Word")
            self.curses.addstr(curses.LINES-8, 0, "Q) Quit")
            self.curses.addstr(curses.LINES-7, 0, "X) Exit Dup Check")

            self.curses.addstr(curses.LINES-1, 0, "?")
            self.curses.refresh()

        while (True):
            # ch = get_character()
            if self.curses:
                ch = chr(self.curses.getch())
            else:
                ch = input("? ")
                ch = (ch + "b")[0]

            if ch == ' ':
                return
            if ch == '?':
                if not self.curses:
                    log.error("HELP:  ) Ignore, D) Delete Word, R) Replace Word, Q) Quit, X) Exit.",
                              additional=0)
            elif ch == 'Q' or ch == 'q':
                if self.curses:
                    self.curses.addstr(curses.LINES-1, 0, "Are you sure you want to abort?")
                    self.curses.refresh()
                    ch = self.curses.getch()
                    ch = chr(ch)
                else:
                    ch = input("Are you sure you want to abort? ")
                    ch = (ch + 'x')[0]
                if ch == 'Y' or ch == 'y':
                    self.endwin()
                    sys.exit(1)

                if self.curses:
                    self.curses.addstr(curses.LINES-1, 0, "?" + ' '*30)
                    self.curses.refresh()
            elif ch == 'D' or ch == 'd':
                if isinstance(line[2], str):
                    element.attrib[line[2]] = self.removeText(element.attrib[line[2]], match,
                                                              element)
                elif words[2]:
                    element.text = self.removeText(element.text, match, element)
                else:
                    element.tail = self.removeText(element.tail, match, element)
                return
            elif ch == 'X' or ch == 'x':
                if self.curses:
                    self.curses.addstr(curses.LINES-1, 0,
                                       "Are you sure you want to exit spell checking?")
                    self.curses.refresh()
                    ch = self.curses.getch()
                    ch = chr(ch)
                else:
                    ch = input("Are you sure you want to exit spell checking? ")
                    ch = (ch + 'x')[0]

                if ch == 'Y' or ch == 'y':
                    raise RfcLintError("Exit Requested")
                if self.curses:
                    self.curses.addstr(curses.LINES-1, 0, "?" + ' '*30)
                    self.curses.refresh()
            elif ch == 'R':
                if self.curses:
                    self.curses.addstr(curses.LINES-1, 0, "Replace with: ")
                    self.curses.refresh()
                    ch = ''
                    while True:
                        ch2 = chr(self.curses.getch())
                        if ch2 == '\n':
                            break
                        ch += ch2
                else:
                    ch = input("Replace with: ")

                if isinstance(line[2], str):
                    element.attrib[line[2]] = self.replaceText(element.attrib[line[2]], ch, match,
                                                               element)
                elif words[2]:
                    element.text = self.replaceText(element.text, ch, match, element)
                else:
                    element.tail = self.replaceText(element.tail, ch, match, element)
                return
            else:
                pass

    def removeText(self, textIn, match, el):
        textOut = textIn[:match.start() + self.offset] + textIn[match.end()+self.offset:]
        self.offset += -(match.end() - match.start())
        return textOut

    def replaceText(self, textIn, replaceWord, match, el):
        startChar = match.start() + self.offset
        while textIn[startChar] == ' ':
            startChar += 1

        textOut = textIn[:startChar] + replaceWord + \
            textIn[match.end()+self.offset:]
        self.offset += len(replaceWord) - (match.end() - startChar)
        return textOut
