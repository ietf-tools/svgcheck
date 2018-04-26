import pycodestyle
import unittest
import os
import shutil
from rfctools_common.parser import XmlRfcParser
from rfctools_common.parser import XmlRfcError, CACHES


class TestParserMethods(unittest.TestCase):

    @unittest.skipIf(True, "it has gone bad - the number of errors is different on different platforms")
    def test_pycodestyle_conformance(self):
        """Test that we conform to PEP8."""
        pep8style = pycodestyle.StyleGuide(quiet=False, config_file="pycode.cfg")
        result = pep8style.check_files(['parser.py', 'log.py', 'utils.py',
                                        'test.py'])
        print ("Error count is {0}".format(result.total_errors))
        self.assertEqual(result.total_errors, 114,
                         "Found code style errors (and warnings).")

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
            print('Unable to parse the XML Document: ' + source)
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
        CACHE = []
        parser = XmlRfcParser("Tests/entity-http.xml", quiet=False,
                              cache_path='Tests/cache', no_network=False)
        clear_cache(parser)
        tree = parser.parse()
        parser.cachingResolver.close_all()
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
        CACHES = []
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

    def test_local_nocache_entity(self):
        """ See that we have a failure if we try to get an uncached item """
        CACHES = []
        parser = XmlRfcParser("Tests/entity-http.xml", quiet=False,
                              cache_path='Tests/cache', no_network=True)
        clear_cache(parser)
        with self.assertRaises(XmlRfcError):
            tree = parser.parse()

    def test_french_xml(self):
        """ Parse file w/ encoding ISO-8859-1 """
        parser = XmlRfcParser("Tests/doc_fr_latin1.xml", quiet=False)
        tree = parser.parse()
        """ self.assertEqual(len(tree.tree.xpath('doc')), 1,
                         "Look for that french tag - not found") """

    def test_utf8_xml(self):
        """ Parse file w/ encoding UTF-8 """
        parser = XmlRfcParser("Tests/doc_utf8.xml", quiet=False)
        tree = parser.parse()

    def test_pi_include(self):
        parser = XmlRfcParser("Tests/pi_include.xml", quiet=False)
        tree = parser.parse()


class TestRegressions(unittest.TestCase):
    def test_local_dtd(self):
        """ Find a dtd in the templates directory """
        parser = XmlRfcParser("Tests/dtd.xml", quiet=False)
        tree = parser.parse()

    def test_network_dtd(self):
        """ Find a dtd using the network """
        CACHES = []
        parser = XmlRfcParser("Tests/network-dtd.xml", quiet=False,
                              cache_path='Tests/cache')
        clear_cache(parser)
        tree = parser.parse()
        parser.cachingResolver.close_all()


def clear_cache(parser):
    parser.delete_cache()


if __name__ == '__main__':
    unittest.main()
