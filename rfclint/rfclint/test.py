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
from rfclint.config import ConfigFile
from lxml import etree

try:
    from configparser import SafeConfigParser, NoSectionError
except ImportError:
    from ConfigParser import SafeConfigParser, NoSectionError

test_program = "rfclint"


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


class Test_Coding(unittest.TestCase):
    def test_pycodestyle_conformance(self):
        """Test that we conform to PEP8."""
        pep8style = pycodestyle.StyleGuide(quiet=False, config_file="pycode.cfg")
        result = pep8style.check_files(['run.py', 'abnf.py', 'config.py', 'spell.py',
                                        'test.py'])
        self.assertEqual(result.total_errors, 0,
                         "Found code style errors (and warnings).")


class TestCommandLineOptions(unittest.TestCase):
    """ Run a set of command line checks to make sure they work """
    def test_get_version(self):
        check_process(self, [sys.executable, test_program, "--version"],
                      "Results/version.out", "Results/version.err",
                      None, None)

    def test_clear_cache(self):
        if not os.path.exists('Temp'):
            os.mkdir('Temp')
        if not os.path.exists('Temp/cache'):
            os.mkdir('Temp/cache')
        shutil.copy('Tests/cache_saved/reference.RFC.1847.xml',
                    'Temp/cache/reference.RFC.1847.xml')
        check_process(self, [sys.executable, test_program, "--clear-cache",
                             "--cache=Temp/cache"],
                      None, None,
                      None, None)
        self.assertFalse(os.path.exists('Temp/cache/reference.RFC.1847.xml'))


class Test_ConfigFile(unittest.TestCase):
    """ Set of tests dealing with the config file """
    def test_abnf_program_change(self):
        """ Change the abnf program name """
        try:
            os.mkdir("Temp")
        except OSError as e:
            pass
        shutil.copyfile("Tests/empty.cfg", "Temp/empty.cfg")
        check_process(self, [sys.executable, test_program, "--configfile=Temp/empty.cfg",
                             "--abnf-program=abnf.foo", "--save-config"],
                      None, None, "Results/abnf.cfg", "Temp/empty.cfg")

    def test_abnf_add_rules(self):
        """ Add one dictionary """
        try:
            os.mkdir("Temp")
        except OSError as e:
            pass
        shutil.copyfile("Tests/empty.cfg", "Temp/empty.cfg")
        check_process(self, [sys.executable, test_program, "--configfile=Temp/empty.cfg",
                             "--abnf-add-rules=otherruleset.abnf", "--save-config"],
                      None, None, "Results/abnf_add_rules.cfg", "Temp/empty.cfg")

    def test_spell_options(self):
        """ Change the spell program name """
        try:
            os.mkdir("Temp")
        except OSError as e:
            pass
        shutil.copyfile("Tests/empty.cfg", "Temp/empty.cfg")
        check_process(self, [sys.executable, test_program, "--configfile=Temp/empty.cfg",
                             "--spell-program=spell.foo", "--save-config"],
                      None, None, "Results/spell.cfg", "Temp/empty.cfg")
        check_process(self, [sys.executable, test_program, "--configfile=Temp/empty.cfg",
                             '--no-suggest', '--save-config'],
                      None, None, 'Results/spell-02.cfg', 'Temp/empty.cfg')
        check_process(self, [sys.executable, test_program, "--configfile=Temp/empty.cfg",
                             '--suggest', '--save-config'],
                      None, None, 'Results/spell-03.cfg', 'Temp/empty.cfg')
        check_process(self, [sys.executable, test_program, "--configfile=Temp/empty.cfg",
                             '--color=red', '--save-config'],
                      None, None, 'Results/spell-04.cfg', 'Temp/empty.cfg')
        check_process(self, [sys.executable, test_program, "--configfile=Temp/empty.cfg",
                             '--color=none', '--save-config'],
                      None, None, 'Results/spell-05.cfg', 'Temp/empty.cfg')

    def test_spell_one_dict(self):
        """ Add one dictionary """
        try:
            os.mkdir("Temp")
        except OSError as e:
            pass
        shutil.copyfile("Tests/empty.cfg", "Temp/empty.cfg")
        check_process(self, [sys.executable, test_program, "--configfile=Temp/empty.cfg",
                             "--spell-program=spell.foo", "--dictionary=dict1",
                             "--save-config"],
                      None, None, "Results/spell-one-dict.cfg", "Temp/empty.cfg")

    def test_spell_two_dict(self):
        """ Add two dictionaries """
        try:
            os.mkdir("Temp")
        except OSError as e:
            pass
        shutil.copyfile("Tests/empty.cfg", "Temp/empty.cfg")
        check_process(self, [sys.executable, test_program, "--configfile=Temp/empty.cfg",
                             "--spell-program=spell.foo", "--dictionary=dict1",
                             "--dictionary=dict2", "--save-config"],
                      None, None, "Results/spell-two-dict.cfg", "Temp/empty.cfg")


class Test_Schema(unittest.TestCase):
    """ Initial set of tests dealing with validity and RNG checking """
    @unittest.skipIf(platform.python_implementation() == "PyPy",
                     "Need version 5.10 for this to work")
    def test_invalid_xml(self):
        """ Load and run with an invalid XML file """
        check_process(self, [sys.executable, test_program, "Tests/bad.xml"],
                      "Results/bad.out", "Results/bad.err", None, None)

    def test_invalid_rng(self):
        """ Load and run w/ an invalid RNG file """
        check_process(self, [sys.executable, test_program, "Tests/bad_rfc.xml"],
                      "Results/bad_rfc.out", "Results/bad_rfc.err", None, None)

    def test_invalid_rng_skip(self):
        """ Load and run w/ an invalid RNG file, skip RNG check """
        check_process(self, [sys.executable, test_program, "--no-rng", "--no-spell",
                             "Tests/bad_rfc.xml"],
                      "Results/bad_rfc_skip.out", "Results/bad_rfc_skip.err", None, None)

    def test_invalid_svg(self):
        """ Load and run w/ a valid RFC, but invalid included SVG file """
        check_process(self, [sys.executable, test_program, "Tests/bad_rfc_svg.xml"],
                      "Results/bad_rfc_svg.out", "Results/bad_rfc_svg.err", None, None)

    def test_clean_rng(self):
        """ Load and run w/ a valid RFC """
        check_process(self, [sys.executable, test_program, "--no-spell", "Tests/rfc.xml"],
                      "Results/clean_rfc.out", "Results/clean_rfc.err", None, None)


class Test_Extract(unittest.TestCase):
    """ Set of tests dealing with extracting code from the source """
    def test_extract_nothing(self):
        """ Try and extract an item which does not exist """
        check_process(self, [sys.executable, test_program, "--extract=zero", "--no-spell",
                             "--no-rng", "Tests/abnf.xml"],
                      "Results/extract_none.out", "Results/extract_none.err", None, None)

    def test_extract_one(self):
        """ Try and extract an item which does not exist """
        check_process(self, [sys.executable, test_program, "--extract=ASN.1", "--no-spell",
                             "--no-rng", "Tests/abnf.xml"],
                      "Results/extract_one.out", "Results/extract_one.err", None, None)

    def test_extract_two(self):
        """ Try and extract an item which does not exist """
        check_process(self, [sys.executable, test_program, "--extract=abnf", "--no-spell",
                             "--no-rng", "Tests/abnf.xml"],
                      "Results/extract_two.out", "Results/extract_two.err", None, None)

    def test_extract_to_file(self):
        """ Try and extract an item which does not exist """
        check_process(self, [sys.executable, test_program, "--extract=abnf",
                             "--out=Temp/extract.txt", "--no-spell", "--no-rng",
                             "Tests/abnf.xml"],
                      "Results/extract_file.out", "Results/extract_file.err",
                      "Results/extract.txt", "Temp/extract.txt")


class Test_Abnf(unittest.TestCase):
    """ Set of tests dealing with the abnf checker """
    def test_no_abnf(self):
        """ No ABFN in the source file """
        check_process(self, [sys.executable, test_program, "--no-spell", "Tests/rfc.xml"],
                      "Results/no-abnf.out", "Results/no-abnf.err", None, None)

    def test_clean_abnf(self):
        """ Clean ABNF in the source file """
        check_process(self, [sys.executable, test_program, "--no-spell", "Tests/abnf-clean.xml"],
                      "Results/abnf-clean.out", "Results/abnf-clean.err", None, None)

    def test_error_one(self):
        """ A single ABNF section w/ an error """
        check_process(self, [sys.executable, test_program, "--no-spell", "Tests/abnf-one.xml"],
                      "Results/abnf-one.out", "Results/abnf-one.err", None, None)

    def test_error_three(self):
        """ Three ABNF sections each w/ an error """
        check_process(self, [sys.executable, test_program, "--no-spell", "Tests/abnf-three.xml"],
                      "Results/abnf-three.out", "Results/abnf-three.err", None, None)

    def test_add_extras(self):
        """ An ABNF object needing additional file """
        check_process(self, [sys.executable, test_program, "--no-spell",
                             "--abnf-add-rules=Tests/abnf-extras.abnf",
                             "Tests/abnf-extras.xml"],
                      "Results/abnf-extras.out", "Results/abnf-extras.err", None, None)

    def test_dont_add_extras(self):
        """ An ABNF object needing additional file, but don't provide it """
        check_process(self, [sys.executable, test_program, "--no-spell",
                             "Tests/abnf-extras.xml"],
                      "Results/abnf-extras-no.out", "Results/abnf-extras-no.err", None, None)

    def test_extras_doesnt_exist(self):
        """ An ABNF object needing additional file, but the one given is not real """
        check_process(self, [sys.executable, test_program, "--no-spell",
                             "--abnf-add-rules=abnf-extras.abnf", "Tests/abnf-extras.xml"],
                      "Results/abnf-extras-not.out", "Results/abnf-extras-not.err", None, None)

    def test_error_one_skip(self):
        """ A single ABNF section w/ an error, but skip checking """
        check_process(self, [sys.executable, test_program, "--no-abnf", "--no-spell",
                             "Tests/abnf-one.xml"],
                      "Results/abnf-skip.out", "Results/abnf-skip.err", None, None)

    def test_error_in_extras(self):
        """ An ABNF object needing an addition file, but that has errors """
        check_process(self, [sys.executable, test_program, "--no-spell",
                             "--abnf-add-rules=Tests/abnf-bad-extras.abnf",
                             "Tests/abnf-extras.xml"],
                      "Results/abnf-bad-extras.out", "Results/abnf-bad-extras.err", None, None)

    def test_no_program(self):
        """ No ABNF executable """
        check_process(self, [sys.executable, test_program, "--abnf-program=no-abnf",
                             "--no-spell", "Tests/abnf-extras.xml"],
                      "Results/abnf-no-program.out", "Results/abnf-no-program.err", None, None)


class Test_Xml(unittest.TestCase):
    @unittest.skipIf(True, "Test is still in progress")
    def test_valid_xml(self):
        check_process(self, [sys.executable, test_program, "--no-rng", "Tests/xml1.xml"],
                      "Results/empty", "Results/empty", None, None)


class Test_Spell(unittest.TestCase):
    """ Set of tests dealing with the spell checker API """
    """
    Disable the following tests because different dictionaries currently cause different
    sets of results to be suggested.  Until we figure out how to deal with this problem
    the tests will always be failing someplace.

    def test_error_one(self):
        "" " Do basic quiet spell checking "" "
        check_process(self, [sys.executable, test_program, "--spell-window=0",
                             "--color=none", "Tests/spell.xml"],
                      "Results/spell-01.out",
                      "Results/spell-01.err" if os.name == 'nt'
                      else "Results/spell-01-60.err", None, None)
    """

    def test_add_context(self):
        """ Do basic quiet spell checking """
        check_process(self, [sys.executable, test_program, "--no-suggest",
                             "--color=none", "Tests/spell.xml"],
                      "Results/spell-context.out",
                      "Results/spell-context.err", None, None)

    def test_error_one_no_suggest(self):
        """ Do basic quiet spell checking """
        check_process(self, [sys.executable, test_program, "--no-suggest", "--spell-window=0",
                             "Tests/spell.xml"],
                      "Results/spell-no-suggest.out", "Results/spell-no-suggest.err", None, None)

    def test_add_dict(self):
        """ Add a simple dictionary with my name """
        check_process(self, [sys.executable, test_program, "--no-suggest", "--spell-window=0",
                             "--dictionary=Tests/schaad.wl", "Tests/spell.xml"],
                      "Results/spell-add-dict.out", "Results/spell-add-dict.err", None, None)

    def test_add_dict_not(self):
        """ Add a simple dictionary which does not exit """
        check_process(self, [sys.executable, test_program, "--no-suggest", "--spell-window=0",
                             "--dictionary=schaad.wl", "Tests/spell.xml"],
                      "Results/spell-add-dict-not.out", "Results/spell-add-dict-not.err",
                      None, None)

    def test_add_personal_dict(self):
        """ Add a simple dictionary with my name """
        check_process(self, [sys.executable, test_program, "--no-suggest", "--spell-window=0",
                             "--personal=Tests/schaad.wl", "Tests/spell.xml"],
                      "Results/spell-add-per.out", "Results/spell-add-per.err", None, None)

    def test_add_personal_dict_not(self):
        """ Add a simple dictionary which does not exist """
        check_process(self, [sys.executable, test_program, "--no-suggest", "--spell-window=0",
                             "--personal=schaad.wl", "Tests/spell.xml"],
                      "Results/spell-add-per-not.out", "Results/spell-add-per-not.err", None, None)

    def test_no_program(self):
        """ No spell executable """
        check_process(self, [sys.executable, test_program, "--spell-program=no-spell",
                             "Tests/spell.xml"],
                      "Results/spell-no-program.out", "Results/spell-no-program.err", None, None)

    # @unittest.skipIf(six.PY3 and os.name == 'nt', "Need to fix the pipe problems first")
    def test_spell_utf8(self):
        """ Need to do some testing of spelling w/ utf-8 characters """
        if sys.platform.startswith('linux'):
            errFile = "Results/spell-utf8-linux.err"
        else:
            errFile = "Results/spell-utf8.err"
        check_process(self, [sys.executable, test_program, "--no-suggest", "--spell-window=0",
                             "--no-rng", "Tests/spell-utf8.xml"],
                      "Results/empty", errFile, None, None)

    @unittest.skipIf(True, "Test is still in progress")
    def test_spell_utf8_with_dict(self):
        """ Need to do some testing of spelling w/ utf-8 characters with utf-8 dictionary """
        check_process(self, [sys.executable, test_program, "--no-suggest", "--spell-window=0",
                             "--no-rng", "--dictionary=Tests/utf8.wl", "Tests/spell-utf8.xml"],
                      "Results/spell-utf8-dict.out", "Results/spell-utf8-dict.err", None, None)


class Test_Spell_Hunspell(unittest.TestCase):
    """ Set of tests dealing with the spell checker API """
    """
    Disable the following tests because different dictionaries currently cause different
    sets of results to be suggested.  Until we figure out how to deal with this problem
    the tests will always be failing someplace.

    def test_error_one(self):
        "" " Do basic quiet spell checking "" "
        check_process(self, [sys.executable, test_program, "--spell-window=0",
                             "--color=none", "--spell-program=hunspell", "Tests/spell.xml"],
                      "Results/spell-01.out",
                      "Results/spell-01.err" if os.name == 'nt'
                      else "Results/spell-01-60.err", None, None)
    """

    def test_add_context(self):
        """ Do basic quiet spell checking """
        check_process(self, [sys.executable, test_program, "--no-suggest",
                             "--color=none", "--spell-program=hunspell", "Tests/spell.xml"],
                      "Results/spell-context.out",
                      ["Results/spell-context-hun.err", "Results/spell-context.err"],
                      None, None)

    def test_error_one_no_suggest(self):
        """ Do basic quiet spell checking """
        check_process(self, [sys.executable, test_program, "--no-suggest", "--spell-window=0",
                             "--spell-program=hunspell", "Tests/spell.xml"],
                      "Results/spell-no-suggest.out",
                      ["Results/spell-no-suggest-hun.err", "Results/spell-no-suggest.err"],
                      None, None)

    def test_add_dict(self):
        """ Add a simple dictionary with my name """
        check_process(self, [sys.executable, test_program, "--no-suggest", "--spell-window=0",
                             "--dictionary=Tests/schaad", "--spell-program=hunspell",
                             "Tests/spell.xml"],
                      "Results/spell-add-dict.out",
                      ["Results/spell-add-dict-hun.err", "Results/spell-add-dict.err"],
                      None, None)

    def test_add_dict_not(self):
        """ Add a simple dictionary which does not exit """
        check_process(self, [sys.executable, test_program, "--no-suggest", "--spell-window=0",
                             "--dictionary=schaad", "--spell-program=hunspell",
                             "Tests/spell.xml"],
                      "Results/spell-add-dict-not.out",
                      ["Results/spell-add-dict-not-hun.err", "Results/spell-add-dict-not.err"],
                      None, None)

    def test_add_personal_dict(self):
        """ Add a simple dictionary with my name """
        check_process(self, [sys.executable, test_program, "--no-suggest", "--spell-window=0",
                             "--personal=Tests/schaad.wl", "--spell-program=hunspell",
                             "Tests/spell.xml"],
                      "Results/spell-add-per.out",
                      ["Results/spell-add-per-hun.err", "Results/spell-add-per.err"],
                      None, None)

    def test_add_personal_dict_not(self):
        """ Add a simple dictionary which does not exist """
        check_process(self, [sys.executable, test_program, "--no-suggest", "--spell-window=0",
                             "--personal=schaad", "--spell-program=hunspell", "Tests/spell.xml"],
                      "Results/spell-add-per-not.out",
                      ["Results/spell-add-per-not-hun.err", "Results/spell-add-per-not.err"],
                      None, None)

    def test_spell_utf8(self):
        """ Need to do some testing of spelling w/ utf-8 characters """
        check_process(self, [sys.executable, test_program, "--no-suggest", "--spell-window=0",
                             "--no-rng", "--spell-program=hunspell", "Tests/spell-utf8.xml"],
                      "Results/empty",
                      ["Results/spell-utf8.err", "Results/spell-utf8-linux-hun.err"], None, None)

    @unittest.skipIf(True, "Test is still in progress")
    def test_spell_utf8_with_dict(self):
        """ Need to do some testing of spelling w/ utf-8 characters with utf-8 dictionary """
        check_process(self, [sys.executable, test_program, "--no-suggest", "--spell-window=0",
                             "--no-rng", "--dictionary=Tests/utf8.wl", "--spell-program=hunspell",
                             "Tests/spell-utf8.xml"],
                      "Results/spell-utf8-dict.out", "Results/spell-utf8-dict.err", None, None)


class Test_Regressions(unittest.TestCase):
    def test_file_dtd(self):
        """ Add a simple dictionary with my name """
        check_process(self, [sys.executable, test_program, "--no-rng", "--no-spell",
                             "Tests/dtd.xml"],
                      "Results/empty", "Results/empty",
                      None, None)


def compare_file(errFile, stderr, displayError):
    if six.PY2:
        with open(errFile, 'r') as f:
            lines2 = f.readlines()
        lines1 = stderr.splitlines(True)
    else:
        with open(errFile, 'r', encoding='utf8') as f:
            lines2 = f.readlines()
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
    if hasError and displayError:
        print("stderr")
        print("".join(result))
        return False
    return True


def check_process(tester, args, stdoutFile, errFiles, generatedFile, compareFile):
    """
    Execute a subprocess using args as the command line.
    if stdoutFile is not None, compare it to the stdout of the process
    if generatedFile and compareFile are not None, compare them to each other
    """

    if args[1][-4:] == '.exe':
        args = args[1:]
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdoutX, stderr) = p.communicate()

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

    if errFiles is not None:
        if isinstance(errFiles, list):
            isClean = True
            for errFile in errFiles:
                isClean &= compare_file(errFile, stderr, False)
            if not isClean:
                compare_file(errFiles[0], stderr, True)
        else:
            returnValue &= compare_file(errFiles, stderr, True)

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
    if os.environ.get('RFCEDITOR_TEST'):
        test_program = "run.py"
    else:
        if os.name == 'nt':
            test_program += '.exe'
        test_program = which(test_program)
        if test_program is None:
            print("Failed to find the rfclint for testing")
            test_program = "run.py"
    unittest.main(buffer=True)
