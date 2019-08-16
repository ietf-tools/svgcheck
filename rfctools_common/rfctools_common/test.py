# -*- coding: utf-8 -*-
# --------------------------------------------------
# Copyright The IETF Trust 2018-2019, All Rights Reserved
# --------------------------------------------------

import pycodestyle
import unittest
import os
import shutil
import subprocess
import six
import re
from rfctools_common.parser import XmlRfcParser, SetCache, GetCache
from rfctools_common.parser import XmlRfcError


class Test_Coding(unittest.TestCase):
    # @unittest.skipIf(True, "it has gone bad - the number of errors is different on different platforms")
    def test_pycodestyle_conformance(self):
        """Test that we conform to PEP8."""
        dir = os.path.basename(os.getcwd())
        dirParent = os.path.dirname(os.getcwd())

        files = [f for f in os.listdir(os.getcwd()) if f[-3:] == '.py']

        pep8style = pycodestyle.StyleGuide(quiet=False, config_file="pycode.cfg")
        result = pep8style.check_files(files)

        self.assertEqual(result.total_errors, 0,
                         "Found code style errors (and warnings).")

        if dir != os.path.basename(dirParent):
            return

        files = [os.path.join("..", f) for f in os.listdir(dirParent) if f[-3:] == '.py']
        pep8style = pycodestyle.StyleGuide(quiet=False, config_file="pycode.cfg")
        result = pep8style.check_files(files)
        print("Error count is {0}".format(result.total_errors))
        self.assertEqual(result.total_errors, 0,
                         "Found code style errors (and warnings).")

    def test_pyflakes_confrmance(self):
        files = [f for f in os.listdir(os.getcwd()) if f[-3:] == '.py']
        dir = os.path.basename(os.getcwd())
        dirParent = os.path.dirname(os.getcwd())
        if dir == os.path.basename(dirParent):
            files2 = [os.path.join("..", f) for f in os.listdir(dirParent) if f[-3:] == '.py']
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
        if dir != os.path.basename(dirParent):
            return
        files = [f for f in os.listdir(os.getcwd()) if f[-3:] == '.py']

        copyright_year_re = r"(?i)Copyright The IETF Trust 201\d-%s, All Rights Reserved" % (2019)

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

        self.assertTrue(passed)


class TestParserMethods(unittest.TestCase):

    def test_simple(self):
        """ Test a simple xml file will load."""
        parse = XmlRfcParser("Tests/simple.xml", quiet=False,
                             cache_path=None, no_network=True)
        parse = parse.parse()

    def test_entity(self):
        """ Test that an entity is loaded."""
        parser = XmlRfcParser("Tests/entity.xml", quiet=False,
                              cache_path=None, no_network=True)
        tree = parser.parse()
        self.assertEqual(len(tree.tree.xpath('good')), 1,
                         "Must be exactly one node named good")

    def test_include(self):
        """ Test that an xi:include is loaded"""
        parser = XmlRfcParser("Tests/include.xml", quiet=False,
                              cache_path=None, no_network=True)
        tree = parser.parse()
        self.assertEqual(len(tree.tree.xpath('good')), 1,
                         "Must be exactly one node named good")

    def test_include2(self):
        """ Test that a two level xi:include is loaded"""
        parser = XmlRfcParser("Tests/include2.xml", quiet=False,
                              cache_path=None, no_network=True)
        tree = parser.parse()
        self.assertEqual(len(tree.tree.xpath('good')), 1,
                         "Must be exactly one node named good")

    def test_remote(self):
        """ Test that a remote https entity can be loaded """
        parser = XmlRfcParser("Tests/entity-http.xml", quiet=False,
                              cache_path=None, no_network=False)
        try:
            tree = parser.parse()
            self.assertEqual(len(tree.tree.xpath('reference')), 1,
                             "Must be exactly one reference node")
        except XmlRfcError as e:
            # print('Unable to parse the XML Document: ' + source)
            print(e)
            self.assertFalse()
        parser.cachingResolver.close_all()

    def test_remote_xinclude(self):
        """ Test that a remote https entity can be loaded """
        parser = XmlRfcParser("Tests/include-http.xml", quiet=False,
                              cache_path=None, no_network=False)
        tree = parser.parse()
        self.assertEqual(len(tree.tree.xpath('reference')), 1,
                         "Must be exactly one reference node")
        parser.cachingResolver.close_all()

    def test_remote_cache_entity(self):
        """ Test that a remote https entity can be cached """
        old = GetCache()
        SetCache([])
        parser = XmlRfcParser("Tests/entity-http.xml", quiet=False,
                              cache_path='Tests/cache', no_network=False)
        clear_cache(parser)
        tree = parser.parse()
        parser.cachingResolver.close_all()
        SetCache(old)
        self.assertEqual(len(tree.tree.xpath('reference')), 1,
                         "Must be exactly one reference node")
        self.assertTrue(os.path.exists('Tests/cache/reference.RFC.1847.xml'))

    def test_remote_cache_xinclude(self):
        """ Test that a remote https entity can be cached """
        parser = XmlRfcParser("Tests/include-http.xml", quiet=False,
                              cache_path='Tests/cache', no_network=False)
        clear_cache(parser)
        tree = parser.parse()
        parser.cachingResolver.close_all()
        self.assertEqual(len(tree.tree.xpath('reference')), 1,
                         "Must be exactly one reference node")
        self.assertTrue(os.path.exists('Tests/cache/reference.RFC.1847.xml'))

    def test_local_cache_entity(self):
        """ Test that an entity in the cache can be used w/o a network """
        old = GetCache()
        SetCache([])
        parser = XmlRfcParser("Tests/entity-http.xml", quiet=False,
                              cache_path='Tests/cache', no_network=True)
        clear_cache(parser)
        if not os.path.exists('Tests/cache'):
            os.mkdir('Tests/cache')
        shutil.copy('Tests/cache_saved/reference.RFC.1847.xml',
                    'Tests/cache/reference.RFC.1847.xml')
        tree = parser.parse()
        self.assertEqual(len(tree.tree.xpath('reference')), 1,
                         "Must be exactly one reference node")
        parser.cachingResolver.close_all()
        SetCache(old)

    def test_local_nocache_entity(self):
        """ See that we have a failure if we try to get an uncached item """
        restore = GetCache()
        SetCache([])
        parser = XmlRfcParser("Tests/entity-http.xml", quiet=False,
                              cache_path='Tests/cache', no_network=True)
        clear_cache(parser)
        with self.assertRaises(XmlRfcError):
            parser.parse()
        SetCache(restore)

    def test_french_xml(self):
        """ Parse file w/ encoding ISO-8859-1 """
        parser = XmlRfcParser("Tests/doc_fr_latin1.xml", quiet=False)
        parser.parse()
        """ self.assertEqual(len(tree.tree.xpath('doc')), 1,
                         "Look for that french tag - not found") """

    def test_utf8_xml(self):
        """ Parse file w/ encoding UTF-8 """
        parser = XmlRfcParser("Tests/doc_utf8.xml", quiet=False)
        parser.parse()

    def test_pi_include(self):
        parser = XmlRfcParser("Tests/pi_include.xml", quiet=False)
        parser.parse()


class TestRegressions(unittest.TestCase):
    def test_local_dtd(self):
        """ Find a dtd in the templates directory """
        parser = XmlRfcParser("Tests/dtd.xml", quiet=False)
        parser.parse()

    def test_network_dtd(self):
        """ Find a dtd using the network """
        old = GetCache()
        # CACHES = []
        SetCache([])
        parser = XmlRfcParser("Tests/network-dtd.xml", quiet=False,
                              cache_path='Tests/cache')
        clear_cache(parser)
        parser.parse()
        SetCache(old)
        parser.cachingResolver.close_all()


def clear_cache(parser):
    parser.delete_cache()


if __name__ == '__main__':
    unittest.main()
