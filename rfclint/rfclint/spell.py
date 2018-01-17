import io
import re
import os
import colorama
import six
import platform
from rfctools_common import log

if six.PY2:
    import subprocess32
    subprocess = subprocess32
else:
    import subprocess


CutNodes = {
    "t":1
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
            if not is_exe(program):
                log.error("The program '{0}' does not exist or is not executable".format(program))
                raise FileNotFoundException(program)
        else:
            print(" OS = {0}".format(os.name))
            if os.name == "nt":
                look_for = "aspell.exe"
            else:
                look_for = "aspell"
            program = which(look_for)
            if not program:
                log.error("Cannot locate the program '{0}' on the path".format(look_for) )
                raise FileNotFoundException(lookfor)

            
        cmdLine = [program, '-a']
        print("   PROGRAM = '{0}'".format(program))
        print("   COMMAND LINE = '{0}'".format(cmdLine))
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
            self.stdin = io.TextIOWrapper( self.p.stdin, encoding='utf-8', line_buffering=True)
            self.stdout = io.TextIOWrapper(self.p.stdout, encoding='utf-8')
        self.stdout.readline()
        # self.stdin.write('!\n')
        self.word_re = re.compile(r'\w+[,.?!]*', re.UNICODE | re.MULTILINE)
        # self.word_re = re.compile(r'\w+', re.UNICODE | re.MULTILINE)

    def close(self):
        self.p.kill()
        self.stdin.close()
        self.stdout.close()
        self.p.wait()
    
    def processLine(self, words):
        line = " ".join(words) + "\n"
        print( "line = " + line)
        self.stdin.write('^ ' + line)
        result = []
        for x in words:
            result.append(self.stdout.readline())
            print("    r = " + result[-1])
        return result

    def processTree(self, tree):
        if tree.tag in CutNodes:
            self.checkTree(tree)
        for node in tree.iterchildren():
            self.processTree(node)

    def checkTree(self, tree):
        (words, where) = self.getWords(tree)
        print (words)
        results = self.processLine(words)

        for i in range(len(results)):
            if results[i][0] != '&':
                continue
            log.warn("{0}:{1}: Misspelled word was found '{2}'".
                     format("FileName.xxx", #where[i].basename,
                            where[i].sourceline, words[i]))

            s = " ".join(words[max(0, i-10):min(len(words), i+10)])
            s = s.replace(words[i], colorama.Fore.GREEN + ">>>" + words[i] + "<<<" + colorama.Style.RESET_ALL)
            log.warn(s)
            log.warn(results[i][results[i].rfind(':')+2:])
            

    def getWords(self, tree):
        body = tree.text
        words = self.word_re.findall(body)
        where = [tree] * len(words)

        for node in tree.iterchildren():
            (w, t) = self.getWords(node)
            words += w
            where += t

            if node.tail:
                w = self.word_re.split(node.tail)
                t = [node] * len(w)
                words += w
                where += t
        return (words, where)
    
        
        
