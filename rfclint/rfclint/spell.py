import io
import re
import os
import errno
import sys
import colorama
import six
import platform
from rfctools_common import log

if six.PY2:
    import subprocess32
    subprocess = subprocess32
else:
    import subprocess


CheckAttributes = {
    "title": ('ascii', 'abbrev'),
    'seriesInfo': {'name', 'asciiName', 'value', 'asciiValue'},
    "author": ('asciiFullname', 'asciiInitials', 'asciiSurname', 'fullname', 'surname', 'initials'),
    'city': {'ascii'},
    'code': {'ascii'},
    'country': {'ascii'},
    'region': {'ascii'},
    'street': {'ascii'},
    'blockquote': {'quotedFrom'},
    'iref': {'item', 'subitem'},
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


class Speller(object):
    """ Object to deal with processing spelling and duplicates """
    def __init__(self, config):
        program = config.get('spell', 'program')
        if program:
            if not which(program):
                log.error("The program '{0}' does not exist or is not executable".format(program))
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), program)
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
                log.error("Cannot locate the program '{0}' on the path".format(look_for))
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), look_for)

        cmdLine = [program, '-a']
        dicts = config.get('spell', 'dictionaries')
        if dicts:
            for dict in dicts:
                cmdLine.append("--add-extra-dicts")
                cmdLine.append(dict)

        self.p = subprocess.Popen(cmdLine,
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        if six.PY2:
            self.stdout = self.p.stdout
            self.stdin = self.p.stdin
        else:
            self.stdin = io.TextIOWrapper(self.p.stdin, encoding='utf-8', line_buffering=True)
            self.stdout = io.TextIOWrapper(self.p.stdout, encoding='utf-8')
        self.stdout.readline()
        # self.stdin.write('!\n')
        self.word_re = re.compile(r'\w[\w,.?!]*', re.UNICODE | re.MULTILINE)
        # self.word_re = re.compile(r'\w+', re.UNICODE | re.MULTILINE)
        self.aspell_re = re.compile(r".\s(\w+)\s(\d+)(\s(\d+): (.+))?", re.UNICODE)

    def close(self):
        self.p.kill()
        self.stdin.close()
        self.stdout.close()
        self.p.wait()

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
        result = []

        for wordSet in allWords:
            self.stdin.write('^ ' + wordSet[0] + '\n')
            # print('in line = ' + wordSet[0])

            index = 0
            running = 0
            while True:
                line = self.stdout.readline().strip()
                # print('out line = ' + line)
                if len(line) == 0:
                    break

                if line[0] == '*':
                    continue

                m = self.aspell_re.match(line)
                if not m:
                    log.error("Internal error trying to match the line '{0}".format(line))
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

                tuple = (line[0], offset, wordSet[1], m.group(1), options)
                result.append(tuple)

        return result

    def processTree(self, tree):
        # log.warn("processTree - look at node {0}".format(tree.tag))
        if tree.tag in CheckAttributes:
            self.checkAttributes(tree)
        if tree.tag in CutNodes:
            self.checkTree(tree)
        for node in tree.iterchildren():
            self.processTree(node)

    def checkTree(self, tree):
        wordSet = self.getWords(tree)
        results = self.processLine(wordSet)

        for r in results:
            log.error("Misspelled word was found '{0}'".
                      format(r[3]), where=r[2])

        # s = " ".join(words[max(0, i-10):min(len(words), i+10)])
        # s = s.replace(words[i], colorama.Fore.GREEN + ">>>" + words[i] + "<<<" +
        #       colorama.Style.RESET_ALL)
        # log.warn(s)
        # log.warn(results[i][results[i].rfind(':')+2:])

    def getWords(self, tree):
        if tree.text:
            for x in tree.text.splitlines():
                ll = x.strip()
                if ll:
                    words = [(ll, tree)]
        else:
            words = []

        for node in tree.iterchildren():
            if node.tag in CutNodes:
                continue
            words += self.getWords(node)

            if node.tail:
                words += [(node.tail, tree)]

        return words

    def checkAttributes(self, tree):
        for attr in CheckAttributes[tree.tag]:
            if attr not in tree.attrib:
                continue
            words = [(tree.attrib[attr], tree)]
            results = self.processLine(words)
            for r in results:
                log.error("Misspelled word '{0}' in attribute '{1}'".format(r[3], attr), where=tree)
