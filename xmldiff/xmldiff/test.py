import pycodestyle
import unittest
import os
import shutil
import difflib
from rfctools_common.parser import XmlRfcParser
from rfctools_common.parser import XmlRfcError
from zzs import EditItem, distance
from DiffNode import DiffRoot, BuildDiffTree, DecorateSourceFile, diffCount


class TestParserMethods(unittest.TestCase):

    def test_pycodestyle_conformance(self):
        """Test that we conform to PEP8."""
        pep8style = pycodestyle.StyleGuide(quiet=False, config_file="pycode.cfg")
        result = pep8style.check_files(['run.py', 'zzs.py', 'DiffNode.py',
                                        'test.py'])
        self.assertEqual(result.total_errors, 0,
                         "Found code style errors (and warnings).")


class TestDistanceMethods(unittest.TestCase):
    """ Set of simple functions to test the distance functions """
    def test_SingleFile(self):
        """ Compare file with self """
        DistanceTest(self, "Tests/SimpleTree.xml", "Tests/SimpleTree.xml",
                     "Results/SimpleDistance.txt", "Results/SimpleDistance.html")

    def test_Add1(self):
        """ Insert one inline node """
        DistanceTest(self, "Tests/SimpleTree.xml", "Tests/Simple-AddNode.xml",
                     "Results/Simple-Add1.txt", "Results/Simple-Add1.html")

    def test_Remove1(self):
        """ Remove one inline node """
        DistanceTest(self, "Tests/Simple-AddNode.xml", "Tests/SimpleTree.xml",
                     "Results/Simple-Remove1.txt", "Results/Simple-Remove1.html")

    def test_Add2(self):
        """ Insert two sibling nodes """
        DistanceTest(self, "Tests/SimpleTree.xml", "Tests/Simple-Add2.xml",
                     "Results/Simple-Add2.txt", "Results/Simple-Add2.html")

    def test_Remove2(self):
        """ Remove two sibling node """
        DistanceTest(self, "Tests/Simple-Add2.xml", "Tests/SimpleTree.xml",
                     "Results/Simple-Remove2.txt", "Results/Simple-Remove2.html")

    def test_Add3(self):
        """ Insert leaf nodes """
        DistanceTest(self, "Tests/Simple.xml", "Tests/SimpleTree.xml",
                     "Results/Simple-Add3.txt", "Results/Simple-Add3.html")

    def test_Remove3(self):
        """ Remove leaf node """
        DistanceTest(self, "Tests/SimpleTree.xml", "Tests/Simple.xml",
                     "Results/Simple-Remove3.txt", "Results/Simple-Remove3.html")

    def test_Add4(self):
        """ Insert four sibling nodes """
        DistanceTest(self, "Tests/SimpleTree.xml", "Tests/Simple-Add3.xml",
                     "Results/Simple-Add4.txt", "Results/Simple-Add4.html")

    def test_Remove4(self):
        """ Remove four sibling node """
        DistanceTest(self, "Tests/Simple-Add3.xml", "Tests/SimpleTree.xml",
                     "Results/Simple-Remove4.txt", "Results/Simple-Remove4.html")

    def test_Add5(self):
        """ Replace text with nodes """
        DistanceTest(self, "Tests/SimpleTree.xml", "Tests/Simple-Add4.xml",
                     "Results/Simple-Add5.txt", "Results/Simple-Add5.html")

    def test_Remove5(self):
        """ Replace nodes w/ text """
        DistanceTest(self, "Tests/Simple-Add4.xml", "Tests/SimpleTree.xml",
                     "Results/Simple-Remove5.txt", "Results/Simple-Remove5.html")

    def test_AddAttr1(self):
        """ Insert attribute """
        DistanceTest(self, "Tests/SimpleTree.xml", "Tests/AttrTree1.xml",
                     "Results/Simple-AddAttr1.txt", "Results/Simple-AddAttr1.html")

    def test_RemoveAddr1(self):
        """ Remove attribute """
        DistanceTest(self, "Tests/AttrTree1.xml", "Tests/SimpleTree.xml",
                     "Results/Simple-RemoveAttr1.txt", "Results/Simple-RemoveAttr1.html")

    def test_RenameAttr1(self):
        """ rename attribute """
        DistanceTest(self, "Tests/AttrTree1.xml", "Tests/AttrTree2.xml",
                     "Results/RenameAttr1.txt", "Results/RenameAttr1.html")

    def test_AddAttr2(self):
        """ Insert attribute """
        DistanceTest(self, "Tests/SimpleTree.xml", "Tests/AttrTree1.xml",
                     "Results/Simple-AddAttr1.txt", "Results/Simple-AddAttr1.html")

    def test_RemoveAddr2(self):
        """ Remove attribute """
        DistanceTest(self, "Tests/AttrTree1.xml", "Tests/AttrTree3.xml",
                     "Results/Simple-RemoveAttr2.txt", "Results/Simple-RemoveAttr2.html")


def DistanceTest(tester, leftFile, rightFile, diffFile, htmlFile):
    """ General distance test function """
    diffCount = 0
    left = XmlRfcParser(leftFile, quiet=True, cache_path=None, no_network=True).parse()
    left = BuildDiffTree(left.tree)
    right = XmlRfcParser(rightFile, quiet=True, cache_path=None, no_network=True).parse()
    right = BuildDiffTree(right.tree)

    editSet = distance(left, right, DiffRoot.get_children,
                       DiffRoot.InsertCost, DiffRoot.DeleteCost, DiffRoot.UpdateCost).toList()
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
    with open(htmlFile, 'r') as f:
        lines2 = f.readlines()
    lines2 = [line.strip() for line in lines2]

    result = list(d.compare(x, lines2))

    hasError = False
    for l in result:
        if l[0:2] == '+ ' or l[0:2] == '- ':
            hasError = True
            break
    if hasError:
        print("\n".join(result))
        tester.assertFalse(hasError, "html differs")


def clear_cache(parser):
    parser.delete_cache()


if __name__ == '__main__':
    unittest.main(buffer=True)