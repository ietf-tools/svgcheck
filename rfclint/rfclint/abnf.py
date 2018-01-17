import io
import subprocess
import re
import os
from rfctools_common import log


class AbnfChecker(object):
    def __init__(self, options):
        self.options = options
        self.abnfProgram = "d:\\Projects\\v3\\rfceditor\\rfclint\\win32\\bap.exe"
        self.abnfProgram = os.path.dirname(os.path.realpath(__file__)) + "../../win32/bap.exe"

    def validate(self, tree):
        stdin = io.StringIO()
        xtract = SourceExtracter(tree, "abnf")
        if not xtract.ExtractToFile(stdin):
            log.note("No ABNF to check")
            return False
        cmds = [self.abnfProgram]
        if options.abnf_add:
            if not os.path.exists(options.abnf_add):
                log.error("Additional ABNF rule file '{0}' does not exist".format(optoins.abnf_add))
                return
            cmds.append("-i")
            cmds.append(options.abnf_add)

        p = subprocess.Popen(cmds, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        (stdout, stderr) = p.communicate(stdin.getvalue().encode('utf-8'))

        print("Return = {0}".format(p.returncode))
        print("STDOUT = {0}".format(stdout.decode('utf-8')))
        print("STDERR = {0}".format(stderr.decode('utf-8')))

        for xxx in xtract.lineOffsets:
            print("--- {0} {1} {2}".format(xxx[0], xxx[1], xxx[2]))

        errs = stderr.decode('utf-8').splitlines()
        for err in errs:
            m = re.match(r"stdin\((\d+):(\d+)\): error: (.*)", err)
            if m:
                print("*** '{0}' '{1}' '{2}'".format(m.group(1), m.group(2), m.group(3)))
                line = int(m.group(1))
                runningLine = 0
                for xxx in xtract.lineOffsets:
                    if line < runningLine + xxx[2]:
                        print("{0}:{1}: ERROR: {2}".format(xxx[0], xxx[1] + line - runningLine,
                                                           m.group(3)))
                        break
                    runningLine += xxx[2]
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
            file.write(item.text)
            lineOffsets.append((item.base, item.sourceline, item.text.count('\n')+1))

        self.lineOffsets = lineOffsets
        return True
