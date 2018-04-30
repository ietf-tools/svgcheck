import pycodestyle
import unittest
import os
import shutil
import difflib
import sys
import subprocess
import six
import inspect
from rfctools_common.parser import XmlRfcParser
from rfctools_common.parser import XmlRfcError
from xmldiff.EditItem import EditItem
from xmldiff.zzs2 import distance
from xmldiff.DiffNode import DiffRoot, BuildDiffTree, DecorateSourceFile, diffCount
from xmldiff.DiffNode import ChangeTagMatching, tagMatching, AddParagraphs

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

    def test_single_default(self):
        if not os.path.exists('Temp'):
            os.mkdir('Temp')
        check_process(self, [sys.executable, xmldiff_program, "--quiet",
                             "-o", "Temp/Single.html", "Tests/Simple.xml", "Tests/SimpleTree.xml"],
                      "Results/Empty.txt", "Results/Empty.txt",
                      "Temp/Single.html", "Results/Single.html")

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


class TestParserMethods(unittest.TestCase):

    def test_pycodestyle_conformance(self):
        """Test that we conform to PEP8."""
        pep8style = pycodestyle.StyleGuide(quiet=False, config_file="pycode.cfg")
        result = pep8style.check_files(['../xmldiff/run.py', '../xmldiff/zzs2.py',
                                        '../xmldiff/DiffNode.py', 'test.py'])
        self.assertEqual(result.total_errors, 0,
                         "Found code style errors (and warnings).")


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

    def test_Table1(self):
        """ Add a layer to a tree """
        global tagMatching

        hold = tagMatching
        ChangeTagMatching(None)
        DistanceTest(self, "Tests/Table1.xml", "Tests/Table2.xml",
                     "Results/Table1.txt", "Results/Table1.html", False)
        ChangeTagMatching(hold)

    def test_Table2(self):
        """ Add a layer to a tree """
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


def DistanceTest(tester, leftFile, rightFile, diffFile, htmlFile, markParagraphs):
    """ General distance test function """
    options = OOO()
    diffCount = 0
    left = XmlRfcParser(leftFile, quiet=True, cache_path=None, no_network=True). \
        parse(strip_cdata=False, remove_comments=False)
    left = BuildDiffTree(left.tree, options)
    if markParagraphs:
        left = AddParagraphs(left)
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
