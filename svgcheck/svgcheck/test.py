import pycodestyle
import unittest
import os
import shutil
from rfctools_common.parser import XmlRfcParser
from rfctools_common.parser import XmlRfcError


class TestParserMethods(unittest.TestCase):

    def test_pycodestyle_conformance(self):
        """Test that we conform to PEP8."""
        pep8style = pycodestyle.StyleGuide(quiet=False, config_file="setup.cfg")
        result = pep8style.check_files(['run.py', 'checksvg.py', 'word_properties.py',
                                        'test.py'])
        self.assertEqual(result.total_errors, 18,
                         "Found code style errors (and warnings).")


def clear_cache(parser):
    parser.delete_cache()


if __name__ == '__main__':
    unittest.main()
