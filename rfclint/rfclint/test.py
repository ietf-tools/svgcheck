import pycodestyle
import platform
import unittest
import os
import shutil
import io
import sys
import subprocess
import difflib
import six
from rfclint.spell import Speller
from lxml import etree


class Test_Coding(unittest.TestCase):
    def test_pycodestyle_conformance(self):
        """Test that we conform to PEP8."""
        pep8style = pycodestyle.StyleGuide(quiet=False, config_file="pycode.cfg")
        result = pep8style.check_files(['run.py', 'abnf.py', 'config.py',
                                        'test.py'])
        self.assertEqual(result.total_errors, 0,
                         "Found code style errors (and warnings).")


class Test_ConfigFile(unittest.TestCase):
    """ Set of tests dealing with the config file """
    def test_abnf_program_change(self):
        """ Change the abnf program name """
        try:
            os.mkdir("Temp")
        except Exception as e:
            pass
        shutil.copyfile("Tests/empty.cfg", "Temp/empty.cfg")
        check_process(self, [sys.executable, "run.py", "--configfile=Temp/empty.cfg",
                             "--abnf-program=abnf.foo", "--save-config"],
                      None, None, "Results/abnf.cfg", "Temp/empty.cfg")


class Test_Schema(unittest.TestCase):
    """ Initial set of tests dealing with validity and RNG checking """
    @unittest.skipIf(platform.python_implementation() == "pypy")
    def test_invalid_xml(self):
        """ Load and run with an invalid XML file """
        check_process(self, [sys.executable, "run.py", "Tests/bad.xml"],
                      "Results/bad.out", "Results/bad.err", None, None)

    def test_invalid_rng(self):
        """ Load and run w/ an invalid RNG file """
        check_process(self, [sys.executable, "run.py", "Tests/bad_rfc.xml"],
                      "Results/bad_rfc.out", "Results/bad_rfc.err", None, None)

    def test_invalid_rng_skip(self):
        """ Load and run w/ an invalid RNG file, skip RNG check """
        check_process(self, [sys.executable, "run.py", "--no-rng", "Tests/bad_rfc.xml"],
                      "Results/bad_rfc_skip.out", "Results/bad_rfc_skip.err", None, None)

    def test_invalid_svg(self):
        """ Load and run w/ a valid RFC, but invalid included SVG file """
        check_process(self, [sys.executable, "run.py", "Tests/bad_rfc_svg.xml"],
                      "Results/bad_rfc_svg.out", "Results/bad_rfc_svg.err", None, None)

    def test_clean_rng(self):
        """ Load and run w/ a valid RFC """
        check_process(self, [sys.executable, "run.py", "Tests/rfc.xml"],
                      "Results/clean_rfc.out", "Results/clean_rfc.err", None, None)


class Test_Extract(unittest.TestCase):
    """ Set of tests dealing with extracting code from the source """
    def test_extract_nothing(self):
        """ Try and extract an item which does not exist """
        check_process(self, [sys.executable, "run.py", "--extract=zero",
                             "--no-rng", "Tests/abnf.xml"],
                      "Results/extract_none.out", "Results/extract_none.err", None, None)

    def test_extract_one(self):
        """ Try and extract an item which does not exist """
        check_process(self, [sys.executable, "run.py", "--extract=ASN.1",
                             "--no-rng", "Tests/abnf.xml"],
                      "Results/extract_one.out", "Results/extract_one.err", None, None)

    def test_extract_two(self):
        """ Try and extract an item which does not exist """
        check_process(self, [sys.executable, "run.py", "--extract=abnf",
                             "--no-rng", "Tests/abnf.xml"],
                      "Results/extract_two.out", "Results/extract_two.err", None, None)

    def test_extract_to_file(self):
        """ Try and extract an item which does not exist """
        check_process(self, [sys.executable, "run.py", "--extract=abnf", "--out=Temp/extract.txt",
                             "--no-rng", "Tests/abnf.xml"],
                      "Results/extract_file.out", "Results/extract_file.err",
                      "Results/extract.txt", "Temp/extract.txt")


class Test_Abnf(unittest.TestCase):
    """ Set of tests dealing with the abnf checker """
    def test_no_abnf(self):
        """ No ABFN in the source file """
        check_process(self, [sys.executable, "run.py", "Tests/rfc.xml"],
                      "Results/no-abnf.out", "Results/no-abnf.err", None, None)


class TestSpellerMethods(unittest.TestCase):
    """ Set of tests dealing with the spell checker API """
    @unittest.skipIf(os.name != 'nt', "spell does not work correctly on Linux")
    def test_spell_line(self):
        speller = Speller()
        output = speller.processLine(['This', 'is', 'a', 'sentance.', ';'])
        print(output)
        speller.close()
        self.assertEqual(len(output), 5, "Wrong number of return values")

    @unittest.skipIf(os.name != 'nt', "spell does not work correctly on Linux")
    def test_spell_line_right(self):
        speller = Speller()
        output = speller.processLine(['This', 'is', 'a', 'sentence.', ';'])
        print(output)
        speller.close()
        self.assertEqual(len(output), 5, "Wrong number of return values")

    @unittest.skipIf(os.name != 'nt', "spell does not work correctly on Linux")
    def test_spell_tree(self):
        speller = Speller()
        with open("Tests/spell1.xml", "r") as f:
            tree = etree.parse(f)
        speller.processTree(tree.getroot())
        speller.close()


def check_process(tester, args, stdoutFile, errFile, generatedFile, compareFile):
    """
    Execute a subprocess using args as the command line.
    if stdoutFile is not None, compare it to the stdout of the process
    if generatedFile and compareFile are not None, compare them to each other
    """

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
            lines2 = [line.replace('Tests/', 'Tests\\') for line in lines2]
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
            lines2 = [line.replace('Tests/', 'Tests\\') for line in lines2]
            lines1 = [line.replace('\r', '') for line in lines1]

        cwd = os.getcwd()
        if os.name == 'nt':
            cwd = cwd.replace('\\', '/')
        lines2 = [line.replace('$$CWD$$', cwd) for line in lines2]

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
        with open(generatedFile, 'r') as f:
            lines2 = f.readlines()

        with open(compareFile, 'r') as f:
            lines1 = f.readlines()

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


if __name__ == '__main__':
    unittest.main(buffer=True)
