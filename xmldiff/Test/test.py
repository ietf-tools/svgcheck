# ----------------------------------------------------
# Copyright The IETF Trust 2018-9, All Rights Reserved
# ----------------------------------------------------

import pycodestyle
import unittest
import os
import shutil
import difflib
import sys
import subprocess
import six
import inspect
import struct
import re
from rfctools_common.parser import XmlRfcParser
from xmldiff.EditItem import EditItem
from xmldiff.zzs2 import distance
from xmldiff.DiffNode import DiffRoot, BuildDiffTree
from xmldiff.DiffNode import ChangeTagMatching, AddParagraphs, SourceFiles
from xmldiff.EditDistance import DoWhiteArray, ComputeEdits

xmldiff_program = "rfc-xmldiff"


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


class OOO(object):
    def __init__(self):
        self.debug = True


class TestCommandLineOptions(unittest.TestCase):
    """ Run a set of command line checks to make sure they work """
    def test_get_version(self):
        check_process(self, [sys.executable, xmldiff_program, "--version"],
                      "Results/Version.out", "Results/Empty.txt",
                      None, None)

    def test_clear_cache(self):
        if not os.path.exists('Temp'):
            os.mkdir('Temp')
        if not os.path.exists('Temp/cache'):
            os.mkdir('Temp/cache')
        shutil.copy('Tests/cache_saved/reference.RFC.1847.xml',
                    'Temp/cache/reference.RFC.1847.xml')
        check_process(self, [sys.executable, xmldiff_program, "--clear-cache",
                             "--cache=Temp/cache"],
                      None, None,
                      None, None)
        self.assertFalse(os.path.exists('Temp/cache/reference.RFC.1847.xml'))

    def test_help(self):
        check_process(self, [sys.executable, xmldiff_program, "--help"],
                      "Results/Help.out", "Results/Empty.txt", None, None)

    def test_base_default(self):
        if not os.path.exists('Temp'):
            os.mkdir('Temp')
        check_process(self, [sys.executable, xmldiff_program, "--quiet",
                             "-o", "Temp/Single.html", "Tests/Simple.xml", "Tests/SimpleTree.xml"],
                      "Results/Empty.txt", "Results/Empty.txt",
                      "Temp/Base.html", "Results/Base.html")

    def test_single(self):
        if not os.path.exists('Temp'):
            os.mkdir('Temp')
        check_process(self, [sys.executable, xmldiff_program, "-t", "single.html", "--quiet",
                             "-o", "Temp/Single.html", "Tests/Simple.xml", "Tests/SimpleTree.xml"],
                      "Results/Empty.txt", "Results/Empty.txt",
                      "Temp/Single.html", "Results/Single.html")

    def test_base(self):
        if not os.path.exists('Temp'):
            os.mkdir('Temp')
        check_process(self, [sys.executable, xmldiff_program, "-t", "base.html", "--quiet",
                             "-o", "Temp/Base.html", "Tests/Simple.xml", "Tests/SimpleTree.xml"],
                      "Results/Empty.txt", "Results/Empty.txt",
                      "Temp/Base.html", "Results/Base.html")


class Test_Coding(unittest.TestCase):

    def test_pycodestyle_conformance(self):
        """Test that we conform to PEP8."""
        dirParent = os.path.dirname(os.getcwd())

        files = [f for f in os.listdir(os.getcwd()) if f[-3:] == '.py' and f[:8] != 'torture.']

        errors = 0
        pep8style = pycodestyle.StyleGuide(quiet=False, config_file="pycode.cfg")
        result = pep8style.check_files(files)

        errors += result.total_errors

        files = [os.path.join(dirParent, f) for f in os.listdir(dirParent) if f[-3:] == '.py']
        pep8style = pycodestyle.StyleGuide(quiet=False, config_file="pycode.cfg")
        result = pep8style.check_files(files)
        errors += result.total_errors

        dirParent = os.path.join(dirParent, "xmldiff")
        files = [os.path.join(dirParent, f) for f in os.listdir(dirParent)
                 if f[-3:] == '.py']
        pep8style = pycodestyle.StyleGuide(quiet=False, config_file="pycode.cfg")
        result = pep8style.check_files(files)
        errors += result.total_errors

        self.assertEqual(errors, 0,
                         "Found code style errors (and warnings).")

    def test_pyflakes_confrmance(self):
        files = [f for f in os.listdir(os.getcwd()) if f[-3:] == '.py' and f[:8] != 'torture.']
        dir = os.path.basename(os.getcwd())
        dirParent = os.path.dirname(os.getcwd())

        files2 = [os.path.join(dirParent, f) for f in os.listdir(dirParent) if f[-3:] == '.py']
        files.extend(files2)

        dir = os.path.join(dirParent, 'xmldiff')
        files2 = [os.path.join(dir, f) for f in os.listdir(dir)
                  if f[-3:] == '.py']
        files.extend(files2)

        files.insert(0, 'pyflakes')

        p = subprocess.Popen(files, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdoutX, stderrX) = p.communicate()
        ret = p.wait()
        if ret > 0:
            if six.PY3:
                stdoutX = stdoutX.decode('utf-8')
                stderrX = stderrX.decode('utf-8')
            print(stdoutX)
            print(stderrX)
            self.assertEqual(ret, 0)

    def test_copyright(self):
        dir = os.path.basename(os.getcwd())
        dirParent = os.path.dirname(os.getcwd())
        if dir != 'Test':
            return
        files = [f for f in os.listdir(os.getcwd()) if f[-3:] == '.py']

        copyright_year_re = r"(?i)Copyright The IETF Trust 201\d-%s, All Rights Reserved" % (9)

        passed = True

        for name in files:
            with open(name) as file:
                try:
                    chunk = file.read(4000)
                except UnicodeDecodeError:
                    print("Error reading file %s" % (name))
                    passed = False
                    continue
                if not re.search(copyright_year_re, chunk):
                    print("No copyright in file %s" % (name))
                    passed = False
                    continue

        files = [f for f in os.listdir(dirParent) if f[-3:] == '.py']

        for name in files:
            with open(os.path.join("..", name)) as file:
                try:
                    chunk = file.read(4000)
                except UnicodeDecodeError:
                    print("Error reading file %s" % (name))
                    passed = False
                    continue
                if not re.search(copyright_year_re, chunk):
                    print("No copyright in file %s" % (name))
                    passed = False
                    continue

        path2 = os.path.join(dirParent, "xmldiff")
        files = [f for f in os.listdir(path2) if f[-3:] == '.py']

        for name in files:
            with open(os.path.join(path2, name)) as file:
                try:
                    chunk = file.read(4000)
                except UnicodeDecodeError:
                    print("Error reading file %s" % (name))
                    passed = False
                    continue
                if not re.search(copyright_year_re, chunk):
                    print("No copyright in file %s" % (name))
                    passed = False
                    continue

        self.assertTrue(passed)


class TestDistanceMethods(unittest.TestCase):
    """ Set of simple functions to test the distance functions """
    def test_SingleFile(self):
        """ Compare file with self """
        DistanceTest(self, "Tests/SimpleTree.xml", "Tests/SimpleTree.xml",
                     "Results/SimpleDistance.txt", "Results/SimpleDistance.html", False)

    def test_Add1(self):
        """ Insert one inline node """
        DistanceTest(self, "Tests/SimpleTree.xml", "Tests/Simple-AddNode.xml",
                     "Results/Simple-Add1.txt", "Results/Simple-Add1.html", False)

    def test_Remove1(self):
        """ Remove one inline node """
        DistanceTest(self, "Tests/Simple-AddNode.xml", "Tests/SimpleTree.xml",
                     "Results/Simple-Remove1.txt", "Results/Simple-Remove1.html", False)

    def test_Add2(self):
        """ Insert two sibling nodes """
        DistanceTest(self, "Tests/SimpleTree.xml", "Tests/Simple-Add2.xml",
                     "Results/Simple-Add2.txt", "Results/Simple-Add2.html", False)

    def test_Remove2(self):
        """ Remove two sibling node """
        DistanceTest(self, "Tests/Simple-Add2.xml", "Tests/SimpleTree.xml",
                     "Results/Simple-Remove2.txt", "Results/Simple-Remove2.html", False)

    def test_Add3(self):
        """ Insert leaf nodes """
        DistanceTest(self, "Tests/Simple.xml", "Tests/SimpleTree.xml",
                     "Results/Simple-Add3.txt", "Results/Simple-Add3.html", False)

    def test_Remove3(self):
        """ Remove leaf node """
        DistanceTest(self, "Tests/SimpleTree.xml", "Tests/Simple.xml",
                     "Results/Simple-Remove3.txt", "Results/Simple-Remove3.html", False)

    def test_Add4(self):
        """ Insert four sibling nodes """
        DistanceTest(self, "Tests/SimpleTree.xml", "Tests/Simple-Add3.xml",
                     "Results/Simple-Add4.txt", "Results/Simple-Add4.html", False)

    def test_Remove4(self):
        """ Remove four sibling node """
        DistanceTest(self, "Tests/Simple-Add3.xml", "Tests/SimpleTree.xml",
                     "Results/Simple-Remove4.txt", "Results/Simple-Remove4.html", False)

    def test_Add5(self):
        """ Replace text with nodes """
        DistanceTest(self, "Tests/SimpleTree.xml", "Tests/Simple-Add4.xml",
                     "Results/Simple-Add5.txt", "Results/Simple-Add5.html", False)

    def test_Remove5(self):
        """ Replace nodes w/ text """
        DistanceTest(self, "Tests/Simple-Add4.xml", "Tests/SimpleTree.xml",
                     "Results/Simple-Remove5.txt", "Results/Simple-Remove5.html", False)

    def test_AddAttr1(self):
        """ Insert attribute """
        DistanceTest(self, "Tests/SimpleTree.xml", "Tests/AttrTree1.xml",
                     "Results/Simple-AddAttr1.txt", "Results/Simple-AddAttr1.html", False)

    def test_RemoveAddr1(self):
        """ Remove attribute """
        DistanceTest(self, "Tests/AttrTree1.xml", "Tests/SimpleTree.xml",
                     "Results/Simple-RemoveAttr1.txt", "Results/Simple-RemoveAttr1.html", False)

    def test_RenameAttr1(self):
        """ rename attribute """
        DistanceTest(self, "Tests/AttrTree1.xml", "Tests/AttrTree2.xml",
                     "Results/RenameAttr1.txt", "Results/RenameAttr1.html", False)

    def test_AddAttr2(self):
        """ Insert attribute """
        DistanceTest(self, "Tests/SimpleTree.xml", "Tests/AttrTree1.xml",
                     "Results/Simple-AddAttr1.txt", "Results/Simple-AddAttr1.html", False)

    def test_RemoveAddr2(self):
        """ Remove attribute """
        DistanceTest(self, "Tests/AttrTree1.xml", "Tests/AttrTree3.xml",
                     "Results/Simple-RemoveAttr2.txt", "Results/Simple-RemoveAttr2.html", False)

    def test_Insert1(self):
        """ Add a layer to a tree """
        DistanceTest(self, "Tests/Simple-Add3.xml", "Tests/Insert1.xml",
                     "Results/Insert1.txt", "Results/Insert1.html", False)

    def test_Insert2(self):
        """ Add a layer to a tree """
        DistanceTest(self, "Tests/Simple-Add3.xml", "Tests/Insert2.xml",
                     "Results/Insert2.txt", "Results/Insert2.html", False)

    def test_Insert3(self):
        """ Add a layer to a tree """
        DistanceTest(self, "Tests/Simple-Add3.xml", "Tests/Insert3.xml",
                     "Results/Insert3.txt", "Results/Insert3.html", False)

    def test_Insert4(self):
        """ Add a layer to a tree """
        DistanceTest(self, "Tests/Simple-Add3.xml", "Tests/Insert4.xml",
                     "Results/Insert4.txt", "Results/Insert4.html", False)

    def test_Insert5(self):
        """ Add a layer to a tree """
        DistanceTest(self, "Tests/Simple-Add3.xml", "Tests/Insert5.xml",
                     "Results/Insert5.txt", "Results/Insert5.html", False)

    def test_Namespace(self):
        """ Add a layer to a tree """
        DistanceTest(self, "Tests/Namespace1.xml", "Tests/Namespace2.xml",
                     "Results/Namespace.txt", "Results/Namespace.xml", False)

    def test_Table1(self):
        """ Add a layer to a tree """
        from xmldiff.DiffNode import tagMatching

        hold = tagMatching
        ChangeTagMatching(None)
        DistanceTest(self, "Tests/Table1.xml", "Tests/Table2.xml",
                     "Results/Table1.txt", "Results/Table1.html", False)
        ChangeTagMatching(hold)

    def test_Table2(self):
        """ Add a layer to a tree """
        """ If the first diff fails, make sure that table1 finished correctly """
        DistanceTest(self, "Tests/Table1.xml", "Tests/Table2.xml",
                     "Results/Table2.txt", "Results/Table2.html", False)

    def test_Cdata(self):
        """ Deal with space presevation """
        DistanceTest(self, "Tests/Cdata1.xml", "Tests/Cdata2.xml",
                     "Results/Cdata1.txt", "Results/Cdata1.html", True)

    def test_Comment1(self):
        """ Deal with space presevation """
        DistanceTest(self, "Tests/Comment1.xml", "Tests/Comment2.xml",
                     "Results/Comment1.txt", "Results/Comment1.html", True)

    def test_Entity1(self):
        """ Deal with entities not being expanded """
        check_process(self, [sys.executable, xmldiff_program, "--no-resolve-entities",
                             "Tests/Entity1.xml", "Tests/Entity2.xml", "-o", "Temp/Entity.html"],
                      "Results/Empty.txt", "Results/Entity.err",
                      "Temp/Entity.html", "Results/Entity.html")

    def test_Prefix1(self):
        """ Deal with space presevation """
        DistanceTest(self, "Tests/Prefix1.xml", "Tests/Prefix2.xml",
                     "Results/Prefix1.txt", "Results/Prefix1.html", True)

    def test_Regress1(self):
        """ Deal with space presevation """
        DistanceTest(self, "Tests/Regress1.xml", "Tests/Regress2.xml",
                     "Results/Regress1.txt", "Results/Regress1.html", True)

    def test_Regress2(self):
        """ Deal with space presevation """
        DistanceTest(self, "Tests/Regress2.xml", "Tests/Regress1.xml",
                     "Results/Regress2.txt", "Results/Regress2.html", True)


class TestOverlappedTrees(unittest.TestCase):
    """ Deal with tests for cases where sub-trees will overlap while merging """
    @unittest.skipIf(os.name == 'nt' and struct.calcsize("P") == 4, "Don't run on Python 32-bit")
    def test_Case1_Forward(self):
        DistanceTest(self, "Tests/LOverlap1.xml", "Tests/ROverlap1.xml",
                     "Results/Case1_Forward.txt", "Results/Case1_Forward.xml", True)

    @unittest.skipIf(os.name == 'nt' and struct.calcsize("P") == 4, "Don't run on Python 32-bit")
    def test_Case1_Backward(self):
        DistanceTest(self, "Tests/ROverlap1.xml", "Tests/LOverlap1.xml",
                     "Results/Case1_Backward.txt", "Results/Case1_Backward.xml", True)

    @unittest.skipIf(os.name == 'nt' and struct.calcsize("P") == 4, "Don't run on Python 32-bit")
    def test_Case2_Forward(self):
        DistanceTest(self, "Tests/LOverlap2.xml", "Tests/ROverlap2.xml",
                     "Results/Case2_Forward.txt", "Results/Case2_Forward.xml", True)

    @unittest.skipIf(os.name == 'nt' and struct.calcsize("P") == 4, "Don't run on Python 32-bit")
    def test_Case2_Backward(self):
        DistanceTest(self, "Tests/ROverlap2.xml", "Tests/LOverlap2.xml",
                     "Results/Case2_Backward.txt", "Results/Case2_Backward.xml", True)


class TestStringFormatting(unittest.TestCase):
    def test_case1(self):
        StringAlignTest(self, "Tests/String1a.txt", "Tests/String1b.txt",
                        "Results/String1.txt", None)


def DistanceTest(tester, leftFile, rightFile, diffFile, htmlFile, markParagraphs):
    """ General distance test function """
    options = OOO()
    SourceFiles.Clear()
    left = XmlRfcParser(leftFile, quiet=True, cache_path=None, no_network=True). \
        parse(strip_cdata=False, remove_comments=False)
    left = BuildDiffTree(left.tree, options)
    if markParagraphs:
        left = AddParagraphs(left)
    SourceFiles.LeftDone()
    right = XmlRfcParser(rightFile, quiet=True, cache_path=None, no_network=True). \
        parse(strip_cdata=False, remove_comments=False)
    right = BuildDiffTree(right.tree, options)
    if markParagraphs:
        right = AddParagraphs(right)

    editSet = distance(left, right, DiffRoot.get_children,
                       DiffRoot.InsertCost, DiffRoot.DeleteCost, DiffRoot.UpdateCost)
    with open(diffFile, 'r') as f:
        lines2 = f.readlines()

    d = difflib.Differ()

    # check that the edit set is the same
    lines2 = [line.strip() for line in lines2]
    lines1 = [edit.toString() for edit in editSet]
    result = list(d.compare(lines1, lines2))

    hasError = False
    for ll in result:
        if ll[0:2] == '+ ' or ll[0:2] == '- ':
            hasError = True
            break
    if hasError:
        print("\n".join(result))
        tester.assertFalse(hasError, "edit map differs")

    # check that the HTML output is the same
    left.applyEdits(editSet)
    x = left.ToString()
    x = x.splitlines()
    x = [line.rstrip() for line in x]
    with open(htmlFile, 'rb') as f:
        lines2 = f.read().decode('utf-8').splitlines()
    lines2 = [line.rstrip() for line in lines2]

    result = list(d.compare(x, lines2))

    hasError = False
    for l in result:
        if l[0:2] == '+ ' or l[0:2] == '- ':
            hasError = True
            break
    if hasError:
        print("\n".join(result))
        tester.assertFalse(hasError, "html differs")


def StringAlignTest(tester, leftFile, rightFile, diffFile, htmlFile):
    """ General string comparison function for text alignments """
    if six.PY2:
        with open(leftFile, "rb") as f:
            leftLines = f.read().decode('utf8').replace("\r\n", "\n")
        with open(rightFile, "rb") as f:
            rightLines = f.read().decode('utf8').replace("\r\n", "\n")
        with open(diffFile, "rb") as f:
            opsLines = f.read().decode('utf8').splitlines()
    else:
        with open(leftFile, "r", encoding="utf8") as f:
            leftLines = f.read()
        with open(rightFile, "r", encoding="utf8") as f:
            rightLines = f.read()
        with open(diffFile, "r", encoding="utf8") as f:
            opsLines = f.read().splitlines()

    leftArray = DoWhiteArray(leftLines)
    rightArray = DoWhiteArray(rightLines)

    ops = ComputeEdits(leftArray, rightArray)

    opLines = [u"{0} {1:2d} {2:2d} {3:2d} {4:2d} '{5}' '{6}'".
               format(op[0], op[1], op[2], op[3], op[4],
                      ''.join(leftArray[op[1]:op[2]]).replace('\n', "\\n"),
                      ''.join(rightArray[op[3]:op[4]]).replace('\n', '\\n'))
               for op in ops]

    d = difflib.Differ()
    result = list(d.compare(opLines, opsLines))

    hasError = False
    for l in result:
        if l[0:2] == '+ ' or l[0:2] == '- ':
            hasError = True
            break

    if hasError:
        # print(generatedFile)
        print(u"\n".join(result))

    tester.assertFalse(hasError, "Comparisons failed")


def check_process(tester, args, stdoutFile, errFile, generatedFile, compareFile):
    """
    Execute a subprocess using args as the command line.
    if stdoutFile is not None, compare it to the stdout of the process
    if generatedFile and compareFile are not None, compare them to each other
    """

    if args[1][-4:] == '.exe':
        args = args[1:]
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdoutX, stderr) = p.communicate()
    p.wait()

    returnValue = True
    if stdoutFile is not None:
        with open(stdoutFile, 'r') as f:
            lines2 = f.readlines()

        if six.PY2:
            lines1 = stdoutX.splitlines(True)
        else:
            lines1 = stdoutX.decode('utf-8').splitlines(True)

        if os.name == 'nt':
            lines2 = [line.replace('Tests/', 'Tests\\').replace('Temp/', 'Temp\\')
                      for line in lines2]
            lines1 = [line.replace('\r', '') for line in lines1]

        d = difflib.Differ()
        result = list(d.compare(lines1, lines2))

        hasError = False
        for l in result:
            if l[0:2] == '+ ' or l[0:2] == '- ':
                hasError = True
                break
        if hasError:
            print("stdout:")
            print("".join(result))
            returnValue = False

    if errFile is not None:
        with open(errFile, 'r') as f:
            lines2 = f.readlines()

        if six.PY2:
            lines1 = stderr.splitlines(True)
        else:
            lines1 = stderr.decode('utf-8').splitlines(True)

        if os.name == 'nt':
            lines2 = [line.replace('Tests/', 'Tests\\').replace('Temp/', 'Temp\\')
                      for line in lines2]
            lines1 = [line.replace('\r', '') for line in lines1]

        d = difflib.Differ()
        result = list(d.compare(lines1, lines2))

        hasError = False
        for l in result:
            if l[0:2] == '+ ' or l[0:2] == '- ':
                hasError = True
                break
        if hasError:
            print("stderr")
            print("".join(result))
            returnValue = False

    if generatedFile is not None:
        template_dir = os.path.abspath(os.path.dirname(inspect.getmodule(EditItem).__file__))
        template_dir = os.path.abspath(os.path.dirname(inspect.getsourcefile(EditItem)))
        if os.name == 'nt':
            template_dir = template_dir.replace('\\', '/')
            template_dir = 'file:///' + template_dir.lower()
        else:
            template_dir = 'file://' + template_dir.lower()

        with open(generatedFile, 'r') as f:
            lines2 = f.readlines()
        lines2 = [line.lower() if 'file://' in line else line for line in lines2]

        with open(compareFile, 'r') as f:
            lines1 = f.readlines()
        lines1 = [line.replace('$TDIR', template_dir) for line in lines1]

        cwd = os.getcwd()
        if os.name == 'nt':
            cwd = cwd.replace('\\', '/')
        lines1 = [line.replace('$$CWD$$', cwd) for line in lines1]

        d = difflib.Differ()
        result = list(d.compare(lines1, lines2))

        hasError = False
        for l in result:
            if l[0:2] == '+ ' or l[0:2] == '- ':
                hasError = True
                break

        if hasError:
            print(generatedFile)
            print("".join(result))
            returnValue = False

    tester.assertTrue(returnValue, "Comparisons failed")


def clear_cache(parser):
    parser.delete_cache()


if __name__ == '__main__':
    if os.environ.get('RFCEDITOR_TEST'):
        xmldiff_program = "../xmldiff/run.py"
    else:
        if os.name == 'nt':
            xmldiff_program += '.exe'
        xmldiff_program = which(xmldiff_program)
        if xmldiff_program is None:
            print("Failed to find the rfc-xmldiff for testing")
            xmldiff_program = "../xmldiff/run.py"

    unittest.main(buffer=True)
