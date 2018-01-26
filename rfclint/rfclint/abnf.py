import sys
import errno
import io
import subprocess
import re
import os
import six
from rfctools_common import log
from rfclint.spell import which


class AbnfChecker(object):
    def __init__(self, config):
        program = config.get('abnf', 'program')
        self.dictionaries = config.getList('abnf', 'addrules')
        if program:
            if not which(program):
                log.error("The program '{0}' does not exist or is not executable".format(program))
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), program)
        else:
            # look on the path first
            look_for = "bap"
            if os.name == "nt":
                look_for = "bap.exe"
            program = which(look_for)

            if not program:
                #  Look for the version that we provide
                if sys.platform == "win32" or sys.platform == "cygwin":
                    program = os.path.dirname(os.path.realpath(__file__)) + \
                              "/../bin/bap.exe"
                else:
                    program = os.path.dirname(os.path.realpath(__file__)) + "/../bin/bap"
                program = which(program)
                if not program:
                    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), bap)
        self.abnfProgram = program

    def validate(self, tree):
        stdin = io.StringIO()
        xtract = SourceExtracter(tree, "abnf")
        if not xtract.ExtractToFile(stdin):
            log.note("No ABNF to check")
            return False
        cmds = [self.abnfProgram, "-q"]

        if self.dictionaries:
            for dict in self.dictionaries:
                if not os.path.exists(dict):
                    log.error("Additional ABNF rule file '{0}' does not exist".format(dict))
                    return
                cmds.append("-i")
                cmds.append(dict)

        p = subprocess.Popen(cmds, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        (stdout, stderr) = p.communicate(stdin.getvalue().encode('utf-8'))

        errs = stderr.decode('utf-8').splitlines()
        for err in errs:
            m = re.match(r"(.+)\((\d+):(\d+)\): error: (.*)", err)
            if m:
                line = int(m.group(2))
                filename = m.group(1)
                if filename == 'stdin':
                    runningLine = -1
                    for xxx in xtract.lineOffsets:
                        if line < runningLine + xxx[2]:
                            log.error(m.group(4), file=xxx[0], line=xxx[1] + line - runningLine)
                            break
                        runningLine += xxx[2] - 1
                else:
                    log.error(m.group(4), file=filename, line=line)
            else:
                log.error(err)
        return True


class SourceExtracter(object):
    def __init__(self, tree, sourceType):
        self.tree = tree
        self.sourceType = sourceType

    def ExtractToMemoryFile(self):
        pass

    def ExtractToFile(self, file):
        """
        Extract the code items to the provided file
        Return True if something was actually extracted
        """

        codeItems = self.tree.getroot().xpath("//sourcecode[@type='{0}']".format(self.sourceType))
        if len(codeItems) == 0:
            return False

        lineOffsets = []
        for item in codeItems:
            if six.PY2:
                file.write(unicode(item.text))
            else:
                file.write(item.text)
            lineOffsets.append((item.base, item.sourceline, item.text.count('\n')+1))

        self.lineOffsets = lineOffsets
        return True
