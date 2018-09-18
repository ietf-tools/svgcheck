import io
import re
import os
import errno
import sys
import colorama
import six
import platform
import codecs
import subprocess
try:
    import curses
    haveCurses = True
except ImportError:
    haveCurses = False
from rfctools_common import log
from rfclint.CursesCommon import CursesCommon


if six.PY2:
    import subprocess32
    subprocess = subprocess32
    input = raw_input
else:
    import subprocess

if os.name == 'nt':
    import msvcrt

    def get_character():
        return msvcrt.getch()
else:
    import tty
    import sys
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


class RfcLintError(Exception):
    """ RFC Lint internal errors """
    def __init__(self, msg, filename=None, line_no=0):
        self.msg = msg
        self.message = msg
        self.position = line_no
        self.filename = filename
        self.line = line_no


def ReplaceWithSpace(exc):
    if isinstance(exc, UnicodeDecodeError):
        return u' '
    elif isinstance(exc, UnicodeEncodeError):
        if six.PY2:
            return ((exc.end - exc.start) * u' ', exc.end)
        else:
            return (bytes((exc.end - exc.start) * [32]), exc.end)
    else:
        raise TypeError("can't handle %s" % type(exc).__name__)


CheckAttributes = {
    "title": ['ascii', 'abbrev'],
    'seriesInfo': ['name', 'asciiName', 'value', 'asciiValue'],
    "author": ['asciiFullname', 'asciiInitials', 'asciiSurname', 'fullname', 'surname', 'initials'],
    'city': ['ascii'],
    'code': ['ascii'],
    'country': ['ascii'],
    'region': ['ascii'],
    'street': ['ascii'],
    'blockquote': ['quotedFrom'],
    'iref': ['item', 'subitem'],
}

CutNodes = {
    'annotation': 1,
    'area': 1,
    'artwork': 2,
    'blockquote': 2,
    'city': 1,
    'cref': 1,
    'code': 1,
    'country': 1,
    'dd': 2,
    'dt': 1,
    'email': 1,
    'keyword': 1,
    'li': 2,
    'name': 1,
    'organization': 1,
    'phone': 1,
    'postalLine': 1,
    'refcontent': 1,
    'region': 1,
    'sourcecode': 1,
    'street': 1,
    "t": 1,
    'td': 2,
    'th': 2,
    "title": 1,
    'uri': 1,
    'workgroup': 1,
}

# colorama.init()

SpellerColors = {
    'green': colorama.Fore.GREEN,
    'none': '',
    'red': colorama.Fore.RED,
    'bright': colorama.Style.BRIGHT
}
# BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE,

byte1 = b'\x31'
byte9 = b'\x39'


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


class Speller(CursesCommon):
    """ Object to deal with processing spelling and duplicates """
    def __init__(self, config):
        CursesCommon.__init__(self, config)
        program = config.get('spell', 'program')
        self.suggest = config.getBoolean('spell', 'suggest', True)
        self.window = config.getInt('spell', 'window', 15)
        coloring = config.get('spell', 'color')
        if coloring and coloring in SpellerColors:
            self.color_start = SpellerColors[coloring]
            self.color_end = colorama.Style.RESET_ALL
            if self.color_start == '':
                self.color_end = self.color_start
        elif os.name == 'nt':
            self.color_start = ''
            self.color_end = ''
        else:
            self.color_start = colorama.Style.BRIGHT
            self.color_end = colorama.Style.RESET_ALL

        if program:
            look_for = which(program)
            if not look_for and os.name == 'nt':
                look_for = which(program + '.exe')
            if not look_for:
                raise RfcLintError("The program '{0}' does not exist or is not executable".
                                   format(program))
            program = look_for
        else:
            if os.name == "nt":
                look_for = "aspell.exe"
                program = which(look_for)
                if not program:
                    program = which("c:\\Program Files (x86)\\Aspell\\bin\\aspell.exe")
            else:
                look_for = "aspell"
                program = which(look_for)
            if not program:
                raise RfcLintError("The program '{0}' does not exist or is not executable".
                                   format(look_for))

        spellBaseName = os.path.basename(program)
        spellBaseName = spellBaseName.replace('.exe', '')

        # I want to know what the program and version really are

        p = subprocess.Popen([program, "-v"], stdout=subprocess.PIPE)
        (versionOut, stderr) = p.communicate()
        """
        if p.returncode != 0:
            raise RfcLintError("The program '{0}' executed with an error code {1}".
                               format(program, p.returncode))
        """

        m = re.match(r".*International Ispell Version [\d.]+ \(but really (\w+) ([\d.]+).*",
                     versionOut.decode('utf-8'))
        if m is None:
            raise RfcLintError("Error starting the spelling program\n{0}".format(line))

        if m.group(1).lower() != spellBaseName:
            raise RfcLintError("Error: The wrong spelling program was started.  Expected"
                               "{0} and got {1}".format(spellBaseName, m.group(1)))

        codecs.register_error('replaceWithSpace', ReplaceWithSpace)

        self.iso8859 = False
        if spellBaseName == 'aspell':
            log.note("xx - " + m.group(2))
            if m.group(2)[:3] == '0.5':
                # This version does not support utf-8
                self.iso8859 = True
                log.note("Use iso8859")
        elif spellBaseName == 'hunspell':
            # minumum version of hunspell is 1.1.6, but that is probably not something
            # we would find in the wild anymore.  We are therefore not going to check it.
            # However, right now the only version I have for Windows does not support utf-8
            # so until I get a better version, force the use of iso8859 there.
            if os.name == 'nt':
                self.iso8859 = True
                log.note("Use iso8859")

        # now let's build the full command

        cmdLine = [program, '-a']  # always use pipe mode
        dicts = config.getList('spell', 'dictionaries')
        if dicts:
            dictList = ''
            for dict in dicts:
                if spellBaseName == 'hunspell':
                    dict = dict + '.dic'
                if os.path.isabs(dict):
                    dict2 = dict
                else:
                    dict2 = os.path.join(os.getcwd(), dict)
                dict2 = os.path.normpath(dict2)
                if not os.path.exists(dict2):
                    log.error("Additional Dictionary '{0}' ignored because it was not found".
                              format(dict.replace('.dic', '')))
                    continue
                if spellBaseName == 'aspell':
                    cmdLine.append("--add-extra-dicts")
                    cmdLine.append(dict2)
                else:
                    dictList = dictList + "," + dict2.replace('.dic', '')
            if spellBaseName == 'hunspell':
                cmdLine.append('-d')
                cmdLine.append("en_US" + dictList)

        dict = config.get('spell', 'personal')
        if dict:
            if os.path.isabs(dict):
                dict2 = dict
            else:
                dict2 = os.path.join(os.getcwd(), dict)
            dict2 = os.path.normpath(dict2)
            if not os.path.exists(dict2):
                log.error("Personal Dictionary '{0}' ignored because it was not found".
                          format(dict))
            else:
                cmdLine.append('-p')
                cmdLine.append(dict2)

        if self.iso8859:
            if spellBaseName == 'aspell':
                cmdLine.append('--encoding=iso8859-1')
            else:
                # Make sure if we have a better version of hunspell that it will do the right thing
                cmdLine.append('-i iso-8859-1')
        elif spellBaseName == 'hunspell':
            cmdLine.append('-i utf-8')

        log.note("spell command = '{0}'".format(" ".join(cmdLine)))
        self.p = subprocess.Popen(cmdLine,
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        if six.PY2:
            if os.name == 'nt':
                self.stdin = codecs.getwriter('iso-8859-1')(self.p.stdin)
                self.stdout = self.p.stdout
            else:
                self.stdin = codecs.getwriter('utf8')(self.p.stdin)
                self.stdout = self.p.stdout
                # self.stdout = codecs.getreader('utf8')(self.p.stdout)
        else:
            if self.iso8859:
                self.stdin = io.TextIOWrapper(self.p.stdin, encoding='iso-8859-1',
                                              errors='replaceWithSpace', line_buffering=True)
                self.stdout = io.TextIOWrapper(self.p.stdout, encoding='iso-8859-1',
                                               errors='replaceWithSpace')
            else:
                self.stdin = io.TextIOWrapper(self.p.stdin, encoding='utf-8', line_buffering=True)
                self.stdout = io.TextIOWrapper(self.p.stdout, encoding='utf-8')

        #  Check that we got a good return
        line = self.stdout.readline()
        log.note(line)

        self.word_re = re.compile(r'(\W*\w+\W*)', re.UNICODE | re.MULTILINE)
        # self.word_re = re.compile(r'\w+', re.UNICODE | re.MULTILINE)
        self.aspell_re = re.compile(r".\s(\S+)\s(\d+)\s*((\d+): (.+))?", re.UNICODE)

        self.spell_re = re.compile(r'\w[\w\'\u00B4\u2019]*\w', re.UNICODE)

        if config.options.output_filename is not None:
            self.ignoreWords = []
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

    def checkWord(self, wordToCheck):
        #  Write word to check to the speller

        newLine = u'^ ' + wordToCheck + u'\n'
        if self.iso8859:
            log.note(u"Pre Encode = " + newLine)
            newLine = newLine.encode('iso-8859-1', 'replaceWithSpace')
            newLine = newLine.decode('iso-8859-1')
        else:
            newLine = newLine  # .encode('utf-8')
            log.note(newLine)
        self.stdin.write(newLine)

        result = []

        #  Read all of the results
        while True:
            line = self.stdout.readline()
            if six.PY2:
                if self.iso8859:
                    #  log.note(" ".join("{:02x}".format(c) for c in line))
                    line = line.decode('iso-8859-1')
                else:
                    line = line.decode('utf-8')
            line = line.strip()
            log.note('spell out line = ' + line)

            #  Empty lines mean that we are done
            if len(line) == 0:
                break

            # '*' means ????
            if line[0] == '*':
                continue

            m = self.aspell_re.match(line)
            if not m:
                log.error("Internal error trying to match the line '{0}'".format(line))
                continue

            if line[0] == '#':
                offset = int(m.group(2))
                options = None
            elif line[0] == '&':
                offset = int(m.group(4))
                options = m.group(5)
            else:
                log.error("internal error - aspell says line is '{0}'".format(line))
                continue

            tuple = (line[0], offset, None, m.group(1), options, 0)
            result.append(tuple)

        return result

    def sendCommand(self, cmd):
        newLine = cmd + u'\n'
        if self.iso8859:
            log.note(u"Pre Encode = " + newLine)
            newLine = newLine.encode('iso-8859-1', 'replaceWithSpace')
            newLine = newLine.decode('iso-8859-1')
        else:
            newLine = newLine  # .encode('utf-8')
            log.note(newLine)
        self.stdin.write(newLine)

    def processLine(self, allWords):
        """
        Process each individual set of words and return the errors found
        allWords is a tuple of (text string, tree element)
        returned is an array of tuples each tuple consisting of
        ( What the error is ('&' or '#'),
          What the word in error is,
          The set of alternative words (None for '#'),
          The offset in the string of the word,
          The word string,
          The tree node
        )
        """
        return []
        result = []
        setNo = 0
        for wordSet in allWords:
            newLine = u'^ ' + wordSet[0] + u'\n'
            if self.iso8859:
                log.note(u"Pre Encode = " + newLine)
                newLine = newLine.encode('iso-8859-1', 'replaceWithSpace')
                newLine = newLine.decode('iso-8859-1')
            else:
                newLine = newLine  # .encode('utf-8')
            log.note(newLine)
            self.stdin.write(newLine)

            index = 0
            running = 0
            while True:
                line = self.stdout.readline()
                if six.PY2:
                    if self.iso8859:
                        #  log.note(" ".join("{:02x}".format(c) for c in line))
                        line = line.decode('iso-8859-1')
                    else:
                        line = line.decode('utf-8')
                line = line.strip()
                log.note('spell out line = ' + line)

                if len(line) == 0:
                    break

                if line[0] == '*':
                    continue

                m = self.aspell_re.match(line)
                if not m:
                    log.error("Internal error trying to match the line '{0}'".format(line))
                    continue

                if line[0] == '#':
                    offset = int(m.group(2))
                    options = None
                elif line[0] == '&':
                    offset = int(m.group(4))
                    options = m.group(5)
                else:
                    log.error("internal error - aspell says line is '{0}'".format(line))
                    continue

                tuple = (line[0], offset, wordSet[1], m.group(1), options, setNo)
                result.append(tuple)
            setNo += 1

        return result

    def getWords(self, tree):
        words = []
        if tree.text:
            words += [(tree.text, tree, True, -1)]

        for node in tree.iterchildren():
            if node.tag not in CutNodes:
                words += self.getWords(node)

            if node.tail:
                words += [(node.tail, node, False, -1)]

        return words

    def processResults(self, wordSet, results, attributeName):
        """  Process the results coming from a spell check operation """

        matchGroups = []
        allWords = []
        if not self.interactive:
            for words in wordSet:
                newline = re.sub(r'\s*\n\s*', ' ',
                                 re.sub(r'\.\s*\n\s*', '.  ', words[0]))
                xx = self.word_re.finditer(newline)
                for w in xx:
                    if w:
                        matchGroups.append((w, words[1], words[2], words[3]))
                        allWords.append(w.group(1))
                        if allWords[-1][-1] not in [' ', '-', "'"]:
                            allWords[-1] += ' '
            if len(allWords) > 0:
                allWords[0] = allWords[0].lstrip()
                allWords[-1] = allWords[-1].rstrip()

        # do the spelling checking
        wordNo = -1
        for words in wordSet:
            xx = self.spell_re.finditer(words[0])
            for w in xx:
                wordNo += 1
                sp = self.checkWord(w.group(0))
                if len(sp) == 0:
                    continue
                if self.interactive:
                    self.Interact(words[1], w, -1, wordSet, words, sp[0])
                else:
                    if attributeName:
                        log.error("Misspelled word '{0}' in attribute '{1}'".format(w.group(0),
                                                                                    attributeName),
                                  where=words[1])
                    else:
                        log.error(u"Misspelled word was found '{0}'".format(w.group(0)),
                                  where=words[1])
                    if self.window > 0:
                        if wordNo >= 0:
                            ctx = ""
                            if wordNo > 0:
                                ctx = "".join(allWords[max(0, wordNo - self.window):wordNo])
                            ctx += self.color_start + allWords[wordNo] + self.color_end
                            if wordNo < len(allWords):
                                ctx += "".join(
                                    allWords[wordNo + 1:
                                             min(wordNo + self.window + 1, len(allWords))])
                            log.error(ctx, additional=2)
                    if self.suggest and sp[0][4]:
                        suggest = " ".join(sp[0][4].split()[0:10])
                        log.error(suggest, additional=2)

    def Interact(self, element, match, srcLine, wordSet, words, spellInfo):
        #
        #  At the request of the RFC editors we use the ispell keyboard mappings
        #
        #  R - replace the misspelled word completely
        #  Space - Accept the word this time only.
        #  A - Accept word for this session.
        #  I - Accept the word, insert private dictionary as is
        #  U - Accept the word, insert private dictionary as lower-case
        #  0-n - Replace w/ one of the suggested words
        #  L - Look up words in the system dictionary - NOT IMPLEMENTED
        #  X - skip to end of the file
        #  Q - quit and don't save the file
        #  ? - Print help
        #

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
            str1 = u"{1}:{2} Misspelled word '{0}' found in attribute '{3}'". \
                        format(match.group(0), fileName, element.sourceline, words[2])
        else:
            str1 = u"{1}:{2} Misspelled word found '{0}'". \
                        format(match.group(0), fileName, element.sourceline)

        if self.curses:
            self.curses.addstr(curses.LINES-15, 0, self.spaceline, curses.A_REVERSE)
            self.curses.addstr(curses.LINES-14, 0, str1.encode('ascii', 'replaceWithONE'))
            self.curses.addstr(curses.LINES-13, 0, self.spaceline, curses.A_REVERSE)
        else:
            log.write("")
            log.error(str1)

        self.writeStringInit()
        for line in wordSet:
            if isinstance(line[2], str):
                text = line[1].attrib[line[2]]
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

        if spellInfo[4] is None:
            suggest = []
        else:
            suggest = spellInfo[4].split(',')

        # list = ""
        # for i in range(min(10, len(suggest))):
        #     list += "{0}) {1} ".format(chr(i + 0x31), suggest[i])

        for i in range(min(10, len(suggest))):
            str1 = "{0}) {1}".format((i+1) % 10, suggest[i].strip())
            if self.curses:
                self.curses.addstr(int(i/2) + curses.LINES-12, int(i % 2)*40, str1)

            else:
                log.write_on_line(str1 + " ")

        if self.curses:
            self.curses.addstr(curses.LINES-6, 0, " ) Ignore")
            self.curses.addstr(curses.LINES-6, 40, "A) Accept Word Always")
            self.curses.addstr(curses.LINES-5, 0, "I) Add to dictionary")
            self.curses.addstr(curses.LINES-5, 40, "U) Add to dictionary lowercase")
            self.curses.addstr(curses.LINES-4, 0, "D) Delete Word")
            self.curses.addstr(curses.LINES-4, 40, "R) Replace Word")
            self.curses.addstr(curses.LINES-3, 0, "Q) Quit")
            self.curses.addstr(curses.LINES-3, 40, "X) Exit Spell Check")
            self.curses.addstr(curses.LINES-2, 0, self.spaceline, curses.A_REVERSE)
            self.curses.addstr(curses.LINES-1, 0, "?")
            self.curses.refresh()
        else:
            log.write("")

        replaceWord = None

        while (True):
            # ch = get_character()
            if self.curses:
                ch = chr(self.curses.getch())
            else:
                ch = input("? ")
                ch = (ch+'b')[0]

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
                    sys.exit(1)
                if self.curses:
                    self.curses.addstr(curses.LINES-1, 0, "?" + ' '*30)
                    self.curses.refresh()
            elif ch == 'A' or ch == 'a':
                self.sendCommand("@"+match.group(0))
                return
            elif ch == 'I' or ch == 'i':
                self.sendCommand("*"+match.group(0))
                return
            elif ch == 'U' or ch == 'u':
                self.sendCommand("&"+match.group(0))
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
            elif ch == 'R' or ch == 'r':
                if self.curses:
                    self.curses.addstr(curses.LINES-1, 0, "Replace with: ")
                    curses.nocbreak()
                    curses.echo()
                    self.curses.refresh()
                    replaceWord = self.curses.getstr()
                    curses.cbreak()
                    curses.noecho()

                    replaceWord = replaceWord.decode('utf-8')
                else:
                    replaceWord = input("Replace with: ")
            elif 0x31 <= ord(ch) and ord(ch) <= 0x39:
                ch = ord(ch) - 0x31
                replaceWord = suggest[ch]
            elif ch == '0':
                replaceWord = suggest[9]
            else:
                pass

            if replaceWord is not None:
                if isinstance(line[2], str):
                    element.attrib[line[2]] = self.replaceText(element.attrib[line[2]],
                                                               replaceWord, match, element)
                elif words[2]:
                    element.text = self.replaceText(element.text, replaceWord, match, element)
                else:
                    element.tail = self.replaceText(element.tail, replaceWord, match, element)
                return

    def replaceText(self, textIn, replaceWord, match, el):
        startChar = match.start() + self.offset
        while textIn[startChar] == ' ':
            startChar += 1

        textOut = textIn[:startChar] + replaceWord + \
            textIn[match.end()+self.offset:]
        self.offset += len(replaceWord) - (match.end() - match.start())
        return textOut
