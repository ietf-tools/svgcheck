import pycodestyle
import unittest
import os
import shutil
import lxml.etree
from rfctools_common.parser import XmlRfcParser
from rfctools_common.parser import XmlRfcError
from rfctools_common import log
import difflib
from svgcheck.checksvg import check
import io


class TestParserMethods(unittest.TestCase):

    def test_pycodestyle_conformance(self):
        """Test that we conform to PEP8."""
        pep8style = pycodestyle.StyleGuide(quiet=False, config_file="pycode.cfg")
        result = pep8style.check_files(['run.py', 'checksvg.py', 'word_properties.py',
                                        'test.py'])
        self.assertEqual(result.total_errors, 0,
                         "Found code style errors (and warnings).")

    def test_circle(self):
        """ Tests/circle.svg: Test a simple example with a small number of required edits """
        test_svg_file(self, "circle.svg")

    def test_rbg(self):
        """ Tests/rgb.svg: Test a simple example with a small number of required edits """
        test_svg_file(self, "rgb.svg")


def test_svg_file(tester, fileName):
    """ Run the basic tests for a single input file """

    basename = os.path.basename(fileName)
    parse = XmlRfcParser("Tests/" + fileName, quiet=True, cache_path=None, no_network=True)
    tree = parse.parse()

    log.write_out = io.StringIO()
    log.write_err = log.write_out
    check(tree.tree.getroot())

    returnValue = check_results(log.write_out, "Results/" + basename.replace(".svg", ".out"))
    tester.assertFalse(returnValue, "Output to console is different")

    result = io.StringIO(lxml.etree.tostring(tree.tree.getroot(),
                                             pretty_print=True).decode('utf-8'))
    returnValue = check_results(result, "Results/" + basename)
    tester.assertFalse(returnValue, "Result from editing the tree is different")


def check_results(file1, file2Name):
    """  Compare two files and say what the differences are or even if there are
         any differences
    """

    with open(file2Name, 'r') as f:
        lines2 = f.readlines()

    file1.seek(0)
    lines1 = file1.readlines()

    d = difflib.Differ()
    result = list(d.compare(lines1, lines2))

    hasError = False
    for l in result:
        if l[0:2] == '+ ' or l[0:2] == '- ':
            hasError = True
            break

    if hasError:
        print("".join(result))

    return hasError


def clear_cache(parser):
    parser.delete_cache()


if __name__ == '__main__':
    unittest.main(buffer=True)
