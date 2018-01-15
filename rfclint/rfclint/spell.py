import subprocess
import io
import re
import colorama
from rfctools_common import log

CutNodes = {
    "t":1
}

# colorama.init()

class Speller(object):
    """ Object to deal with processing spelling and duplicates """
    def __init__(self):
        self.p = subprocess.Popen(['c:/Program Files (x86)/Aspell/bin/aspell.exe ', '-a'],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE)
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
    
        
        
