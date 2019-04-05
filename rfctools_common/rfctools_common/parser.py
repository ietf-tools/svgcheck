# --------------------------------------------------
# Copyright The IETF Trust 2011, All Rights Reserved
# --------------------------------------------------

""" Public XML parser module """

import io
import re
import os
import codecs
import shutil
import six
import time
import requests
import lxml.etree
from rfctools_common import log
from rfctools_common import utils
from optparse import Values


try:
    from urllib.parse import urlparse, urljoin
except ImportError:
    from urlparse import urlparse, urljoin

try:
    import debug
    assert debug
except ImportError:
    pass

__all__ = ['XmlRfcParser', 'XmlRfc', 'XmlRfcError']

CACHES       = ['/var/cache/xml2rfc', '~/.cache/xml2rfc']  # Ordered by priority
CACHE_PREFIX = ''
NET_SUBDIRS  = ['bibxml', 'bibxml2', 'bibxml3', 'bibxml4', 'bibxml5']

Default_options = Values(defaults={
    'verbose':False,
    'no_network':False,
    'vocabulary':'v3',
    'cache':None,
    'quiet':False
})


class XmlRfcError(Exception):
    """ Application XML errors with positional information

        This class attempts to mirror the API of lxml's error class
    """
    def __init__(self, msg, filename=None, line_no=0):
        self.msg = msg
        # This mirrors lxml error behavior, but we can't capture column
        self.position = (line_no, 0)
        # Also match lxml.etree._LogEntry attributes:
        self.message = msg
        self.filename = filename
        self.line = line_no

    def __str__(self):
        return self.msg

class CachingResolver(lxml.etree.Resolver):
    """ Custom ENTITY request handler that uses a local cache """
    def __init__(self, cache_path=None, library_dirs=None, source=None,
                 templates_path='templates', verbose=None, quiet=None,
                 no_network=None, network_locs=[
                     'https://xml2rfc.tools.ietf.org/public/rfc/',
                     'http://xml2rfc.tools.ietf.org/public/rfc/',
                 ],
                 rfc_number=None, options=Default_options):
        self.quiet = quiet if quiet != None else options.quiet
        self.verbose = verbose if verbose != None else options.verbose
        self.no_network = no_network if no_network != None else options.no_network
        self.cache_path = cache_path if cache_path != None else options.cache
        self.source = source
        self.library_dirs = library_dirs
        self.templates_path = templates_path
        self.network_locs = network_locs
        self.include = False
        self.rfc_number = rfc_number
        self.cache_refresh_secs = (60*60*24*14) # 14 days
        self.options = options

        self.file_handles = []

        # Get directory of source
        if self.source:
            if isinstance(self.source, six.string_types):
                self.source_dir = os.path.abspath(os.path.dirname(self.source))
            else:
                self.source_dir = os.path.abspath(os.path.dirname(self.source.name))
        else:
            self.source_dir = None

        # Determine cache directories to read/write to
        self.read_caches = [os.path.expanduser(path) for path in CACHES]
        self.write_cache = None
        if self.cache_path:
            # Explicit directory given, set as first directory in read_caches
            self.read_caches.insert(0, self.cache_path)
        # Try to find a valid directory to write to by stepping through
        # Read caches one by one
        for dir in self.read_caches:
            if os.path.exists(dir) and os.access(dir, os.W_OK):
                self.write_cache = dir
                break
            else:
                try:
                    os.makedirs(dir)
                    log.note('Created cache directory at', dir)
                    self.write_cache = dir
                except OSError:
                    # Can't write to this directory, try the next one
                    pass
        if not self.write_cache:
            log.warn('Unable to find a suitible cache directory to '
                            'write to, trying the following directories:\n ',
                            '\n  '.join(self.read_caches),
                            '\nTry giving a specific directory with --cache.')
        else:
            # Create the prefix directory if it doesnt exist
            if CACHE_PREFIX != None and len(CACHE_PREFIX) > 0:
                pdir = os.path.join(self.write_cache, CACHE_PREFIX)
                if not os.path.exists(pdir):
                    os.makedirs(pdir)

        self.sessions = {}

    def delete_cache(self, path=None):
        # Explicit path given?
        caches = path and [path] or self.read_caches
        for dir in caches:
            path = os.path.join(dir, CACHE_PREFIX)
            if os.access(path, os.W_OK):
                shutil.rmtree(path)
                log.write('Deleted cache directory at', path)

    def resolve(self, request, public_id, context):
        """ Called internally by lxml """
        if not request:
            # Not sure why but sometimes LXML will ask for an empty request,
            # So lets give it an empty response.
            return None
        # If the source itself is requested, return as-is
        if request == self.source:
            return self.resolve_filename(request, context)
        if request == u"internal:/rfc.number":
            if self.rfc_number:
                return self.resolve_string(self.rfc_number, context)
            return self.resolve_string("XXXX", context)
        if not urlparse(request).netloc:
            # Format the request from the relative path of the source so that
            # We get the exact same path as in the XML document
            if request.startswith("file:"):
                request = urlparse(request)
                request = request[2]
                if request[2] == ':':
                    request = request[1:]

            try:
                # The following code plays with files which are in the Template
                # directory.  a plain file name (dtd) will be returned with
                # the path of the current source file.  If the file has the
                # current source path and the file does not exist, strip the path
                # so that we can do searches in other locations.
                if not os.path.exists(request) and \
                        os.path.normpath(os.path.dirname(request)) == self.source_dir:
                    request = os.path.relpath(request, self.source_dir)
            except ValueError:
                pass
        path = self.getReferenceRequest(request)
        if path[1] is not None:
            #
            # This code allows for nested includes to work correctly as we need
            # to have the correct path name for the file to be passed in.
            # This really should be done with the function rseolve_file, but this
            # causing a crash on exit from the test.py in this directory.  The
            # rest of the time it appears to work correctly.  However using the
            # string version does the same thing, just maybe not as well.
            # I think that this is a bug in lxml where the FILE * handle is
            # being messed up in terms of reference counting.
            #
            with open(path[0], "rb") as f:
                file = f.read()
            if file is not None:
                return self.resolve_string(file, context, base_url=path[1])
        return self.resolve_filename(path[0], context)

    def getReferenceRequest(self, request, include=False, line_no=0):
        """ Returns the correct and most efficient path for an external request

            To determine the path, the following algorithm is consulted:

            If REQUEST ends with '.dtd' or '.ent' then
              If REQUEST is an absolute path (local or network) then
                Return REQUEST
            Else
              Try TEMPLATE_DIR + REQUEST, otherwise
              Return SOURCE_DIR + REQUEST
            Else
              If REQUEST doesn't end with '.xml' then append '.xml'
              If REQUEST is an absolute path (local or network) then
                Return REQUEST
              Else
                If REQUEST contains intermediate directories then
                  Try each directory in LOCAL_LIB_DIRS + REQUEST, otherwise
                  Try NETWORK + REQUEST
                Else (REQUEST is simply a filename)
                  [Recursively] Try each directory in LOCAL_LIB_DIRS + REQUEST, otherise
                  Try each explicit (bibxml, bibxml2...) subdirectory in NETWORK + REQUEST

            Finally if the path returned is a network URL, use the cached
            version or create a new cache.

            - REQUEST refers to the full string of the file asked for,
            - TEMPLATE_DIR refers to the applications 'templates' directory,
            - SOURCE_DIR refers to the directory of the XML file being parsed
            - LOCAL_LIB_DIRS refers to a list of local directories to consult,
              on the CLI this is set by $XML_LIBRARY, defaulting to
              ['/usr/share/xml2rfc'].  On the GUI this can be configured
              manually but has the same initial defaults.
            - NETWORK refers to the online citation library.  On the CLI this
              is http://xml2rfc.ietf.org/public/rfc/.  On the GUI this
              can be configured manually but has the same initial default.

            The caches in read_dirs are consulted in sequence order to find the
            request.  If not found, the request will be cached at write_dir.

            This method will throw an lxml.etree.XMLSyntaxError to be handled
            by the application if the reference cannot be properly resolved
        """
        self.include = include  # include state
        tried_cache = False
        attempts = []  # Store the attempts
        original = request  # Used for the error message only
        result = None  # Our proper path
        if request.endswith('.dtd') or request.endswith('.ent'):
            if os.path.isabs(request):
                # Absolute request, return as-is
                attempts.append(request)
                result = request
            elif urlparse(request).netloc:
                paths = [request]
                # URL requested, cache it
                origloc = urlparse(paths[0]).netloc
                if True in [urlparse(loc).netloc == urlparse(paths[0]).netloc
                            for loc in self.network_locs]:
                    for loc in self.network_locs:
                        newloc = urlparse(loc).netloc
                        for path in paths:
                            path = path.replace(origloc, newloc)
                            attempts.append(path)
                            result = self.cache(path)
                            if result:
                                break
                        if result:
                            break
                else:
                    for path in paths:
                        attempts.append(request)
                        result = self.cache(request)
                        if result:
                            break
                if not result and self.no_network:
                    log.warn("Document not found in cache, and --no-network specified"
                             " -- couldn't resolve %s" % request)
                tried_cache = True
            else:
                basename = os.path.basename(request)
                # Look for dtd in templates directory
                attempt = os.path.join(self.templates_path, basename)
                attempts.append(attempt)
                if os.path.exists(attempt):
                    result = attempt
                else:
                    # Default to source directory
                    result = os.path.join(self.source_dir, basename)
                    attempts.append(result)
        else:
            if self.options and self.options.vocabulary == 'v3':
                paths = [request]
            elif not request.endswith('.xml'):
                paths = [request, request + '.xml']
            else:
                paths = [request]
            if os.path.isabs(paths[0]):
                # Absolute path, return as-is
                for path in paths:
                    attempts.append(path)
                    result = path
                    if os.path.exists(path):
                        break
            elif urlparse(paths[0]).netloc:
                # URL requested, cache it
                origloc = urlparse(paths[0]).netloc
                if True in [urlparse(loc).netloc == urlparse(paths[0]).netloc for loc in self.network_locs]:
                    for loc in self.network_locs:
                        newloc = urlparse(loc).netloc
                        for path in paths:
                            path = path.replace(origloc, newloc)
                            attempts.append(path)
                            result = self.cache(path)
                            if result:
                                break
                        if result:
                            break
                else:
                    for path in paths:
                        attempts.append(path)
                        result = self.cache(path)
                        if result:
                            break
                if not result:
                    if self.options and self.options.vocabulary == 'v3' \
                       and not request.endswith('.xml'):
                        log.warn("The v3 formatters require full explicit URLs of external "
                                 "resources.  Did you forget to add '.xml' (or some other extension)?")
                        result = attempt
                    elif self.no_network:
                        log.warn("Document not found in cache, and --no-network specified -- couldn't resolve %s" % request)
                tried_cache = True
            else:
                if os.path.dirname(paths[0]):
                    # Intermediate directories, only do flat searches
                    for dir in self.library_dirs:
                        # Try local library directories
                        for path in paths:
                            attempt = os.path.join(dir, path)
                            attempts.append(attempt)
                            if os.path.exists(attempt):
                                result = attempt
                                break                    

                    if not result:
                        # Try network location
                        for loc in self.network_locs:
                            for path in paths:
                                url = urljoin(loc, path)
                                attempts.append(url)
                                result = self.cache(url)
                                if result:
                                    break
                            if result:
                                break
                        tried_cache = True
                        if not result and self.no_network:
                            log.warn("Document not found in cache, and --no-network specified -- couldn't resolve %s" % request)

                        # if not result:
                        #     # Document didn't exist, default to source dir
                        #     result = os.path.join(self.source_dir, request)
                        #     attempts.append(result)
                else:
                    # Hanging filename
                    for dir in self.library_dirs:
                        # NOTE: Recursion can be implemented here
                        # Try local library directories
                        for path in paths:
                            attempt = os.path.join(dir, path)
                            attempts.append(attempt)
                            if os.path.exists(attempt):
                                result = attempt
                                break
                    if not result:
                        # Try network subdirs
                        for subdir in NET_SUBDIRS:
                            for loc in self.network_locs:
                                for path in paths:
                                    url = urljoin(loc, subdir + '/' + path)
                                    attempts.append(url)
                                    result = self.cache(url)
                                    if result:
                                        break
                                if result:
                                    break
                            tried_cache = True
                            if result:
                                break
                        if not result and self.no_network:
                            log.warn("Document not found in cache, and --no-network specified -- couldn't resolve %s" % request)
                    # if not result:
                    #     # Default to source dir
                    #     result = os.path.join(self.source_dir, request)
                    #     attempts.append(result)

        # Verify the result -- either raise exception or return it
        if not result or (not os.path.exists(result) and not urlparse(original).netloc):
            if os.path.isabs(original):
                log.warn('The reference "' + original + '" was requested with an absolute path, but not found '
                    'in that location.  Removing the path component will cause xml2rfc to look for '
                    'the file automatically in standard locations.')
            # Couldn't resolve.  Throw an exception
            error = XmlRfcError('Unable to resolve external request: '
                                + '"' + original + '"', line_no=line_no, filename=self.source)
            if self.verbose and len(attempts) > 1:
                # Reveal attemps
                error.msg += ', trying the following location(s):\n    ' + \
                             '\n    '.join(attempts)
            raise error
        else:
            if not tried_cache:
                # Haven't printed a verbose messsage yet
                typename = self.include and 'include' or 'entity'
                log.note('Resolving ' + typename + '...', result)
            if tried_cache:
                return [result, original]
            return [result, None]

    def cache(self, url):
        """ Return the path to a cached URL

            Checks for the existence of the cache and creates it if necessary.
        """
        scheme, netloc, path, params, query, fragment = urlparse(url)
        basename = os.path.basename(path)
        typename = self.include and 'include' or 'entity'
        # Try to load the URL from each cache in `read_cache`
        for dir in self.read_caches:
            cached_path = os.path.join(dir, CACHE_PREFIX, basename)
            if os.path.exists(cached_path):
                if os.path.getmtime(cached_path) < (time.time() - self.cache_refresh_secs) and not self.no_network:
                    log.note('Cached version at %s too old; will refresh cache for %s %s' % (cached_path, typename, url))
                    break
                else:
                    log.note('Resolving ' + typename + '...', url)
                    log.note('Loaded from cache', cached_path)
                    return cached_path

        log.note('Resolving ' + typename + '...', url)
        if self.no_network:
            # No network activity
            log.note("URL not retrieved because no-network option set")
            return ''

        if netloc not in self.sessions:
            self.sessions[netloc] = requests.Session()
        session = self.sessions[netloc]
        r = session.get(url)
        for rr in r.history + [r, ]:
            log.note(' ... %s %s' % (rr.status_code, rr.url))
        if r.status_code == 200:
            if self.write_cache:
                text = r.text.encode('utf8')
                try:
                    xml = lxml.etree.fromstring(text)
                    if self.validate_ref(xml):
                        xml.set('{%s}base'%xml2rfc.utils.namespaces['xml'], r.url)
                        text = lxml.etree.tostring(xml, encoding='utf8')
                except Exception as e:
                    pass
                write_path = os.path.normpath(os.path.join(self.write_cache,
                                                           CACHE_PREFIX, basename))
                with codecs.open(write_path, 'w', encoding='utf-8') as cache_file:
                    cache_file.write(text.decode('utf8'))
                log.note('Added file to cache: ', write_path)
                r.close()
                return write_path
            else:
                r.close()
                return url
        else:
            # Invalid URL -- Error will be displayed in getReferenceRequest
            log.note("URL retrieval failed with status code %s for '%s'" % (r.status_code, r.url))
            return ''

    def close_all(self):
        for key in self.sessions:
            self.sessions[key].close()
        self.sessions = {}
        for f in self.file_handles:
            f.close()


class AnnotatedElement(lxml.etree.ElementBase):
    pis = None

    def get(self, key, default=None):
        value = super(AnnotatedElement, self).get(key, default)
        if value == default:
            return value
        else:
            return six.text_type(value)


class XmlRfcParser:

    nsmap = {
        'xi':   'http://www.w3.org/2001/XInclude',
    }

    """ XML parser container with callbacks to construct an RFC tree """
    def __init__(self, source, verbose=None, quiet=None, options=Default_options,
                 cache_path=None, templates_path=None, library_dirs=None,
                 no_xinclude=False,
                 no_network=None, network_locs=[
                     'https://xml2rfc.tools.ietf.org/public/rfc/',
                     'http://xml2rfc.tools.ietf.org/public/rfc/',
                 ],
                 resolve_entities=True,
                 preserve_all_white=False,
                 attribute_defaults = True
                 ):
        self.options = options
        self.quiet = quiet if quiet != None else options.quiet
        self.verbose = verbose if verbose != None else options.verbose
        self.no_network = no_network if no_network != None else options.no_network
        self.cache_path = cache_path or options.cache
        self.source = source
        self.network_locs = network_locs
        self.no_xinclude = no_xinclude
        self.resolve_entities = resolve_entities
        self.preserve_all_white = preserve_all_white
        self.attribute_defaults = attribute_defaults

        # Initialize templates directory
        self.templates_path = templates_path or \
                              os.path.join(os.path.dirname(__file__),
                                           'templates')
        if options and options.vocabulary == 'v2':
            self.default_dtd_path = os.path.join(self.templates_path, 'rfc2629.dtd')
            self.default_rng_path = None
        else:
            self.default_dtd_path = None
            self.default_rng_path = os.path.join(self.templates_path, 'rfc7991.rng')

        for prefix, value in self.nsmap.items():
            lxml.etree.register_namespace(prefix, value)

        # If library dirs werent explicitly set, like from the gui, then try:
        #   1. $XML_LIBRARY environment variable as a delimited list
        #   2. Default to /usr/share/xml2rfc
        # Split on colon or semi-colon delimiters
        if not library_dirs:
            library_dirs = os.environ.get('XML_LIBRARY', '/usr/share/xml2rfc:')
        self.library_dirs = []
        for raw_dir in re.split(':|;', library_dirs):
            # Convert empty directory to source dir
            if raw_dir == '':
                raw_dir = os.path.abspath(os.path.dirname(self.source))
            else:
                raw_dir = os.path.normpath(os.path.expanduser(raw_dir))
            # Add dir if its unique
            if raw_dir not in self.library_dirs:
                self.library_dirs.append(raw_dir)

        # Initialize the caching system.  We'll replace this later if parsing.
        self.cachingResolver = CachingResolver(cache_path=self.cache_path,
                                        library_dirs=self.library_dirs,
                                        templates_path=self.templates_path,
                                        source=self.source,
                                        network_locs=self.network_locs,
                                        verbose=self.verbose,
                                        quiet=self.quiet,
                                        options=options,
                                    )

    def delete_cache(self, path=None):
        self.cachingResolver.delete_cache(path=path)

    def parse(self, remove_comments=True, remove_pis=False, quiet=False, strip_cdata=True):
        """ Parses the source XML file and returns an XmlRfc instance """
        if not (self.quiet or quiet):
            log.write('Parsing file', os.path.normpath(self.source))

        if six.PY2:
            with open(self.source, "rU") as f:
                self.text = f.read()
        else:
            with open(self.source, "rb", newline=None) as f:
                self.text = f.read()

        # Get an iterating parser object
        file = six.BytesIO(self.text)
        file.name = os.path.join(os.path.abspath(  os.path.dirname(self.source)), os.path.basename(self.source))
        context = lxml.etree.iterparse(file,
                                      dtd_validation=False,
                                      load_dtd=True,
                                      attribute_defaults=self.attribute_defaults,
                                      no_network=self.no_network,
                                      remove_comments=remove_comments,
                                      remove_pis=remove_pis,
                                      remove_blank_text=True,
                                      resolve_entities=False,
                                      strip_cdata=strip_cdata,
                                      events=("start",),
                                      tag="rfc",
                                  )
        # resolver without knowledge of rfc_number:
        caching_resolver = CachingResolver(cache_path=self.cache_path,
                                        library_dirs=self.library_dirs,
                                        templates_path=self.templates_path,
                                        source=self.source,
                                        no_network=self.no_network,
                                        network_locs=self.network_locs,
                                        verbose=self.verbose,
                                        quiet=self.quiet,
                                        options=self.options,
                                     )
        context.resolvers.add(caching_resolver)

        # Get hold of the rfc number (if any) in the rfc element, so we can
        # later resolve the "&rfc.number;" entity.
        self.rfc_number = None
        self.format_version = None
        try:
            for action, element in context:
                if element.tag == "rfc":
                    self.rfc_number = element.attrib.get("number", None)
                    self.format_version = element.attrib.get("version", None)
                    break
        except lxml.etree.XMLSyntaxError as e:
            pass
            # log.warn("Parsing Error: %s" % e)
        except ValueError as e:
            if e.message == "I/O operation on closed file":
                pass

        if self.format_version == "3":
            self.default_dtd_path = None
            self.default_rng_path = os.path.join(self.templates_path, 'rfc7991.rng')

        # now get a regular parser, and parse again, this time resolving entities
        parser = lxml.etree.XMLParser(dtd_validation=False,
                                      load_dtd=True,
                                      attribute_defaults=self.attribute_defaults,
                                      no_network=self.no_network,
                                      remove_comments=remove_comments,
                                      remove_pis=remove_pis,
                                      remove_blank_text=not self.preserve_all_white,
                                      # remove_blank_text=True,
                                      resolve_entities=self.resolve_entities,
                                      strip_cdata=strip_cdata)

        # Initialize the caching system
        self.cachingResolver = CachingResolver(cache_path=self.cache_path,
                                        library_dirs=self.library_dirs,
                                        templates_path=self.templates_path,
                                        source=self.source,
                                        no_network=self.no_network,
                                        network_locs=self.network_locs,
                                        verbose=self.verbose,
                                        quiet=self.quiet,
                                        rfc_number=self.rfc_number,
                                        options=self.options
        )

        # Add our custom resolver
        parser.resolvers.add(self.cachingResolver)

        # Use our custom element class, which holds the state of PI settings
        # at this point in the xml tree
        element_lookup = lxml.etree.ElementDefaultClassLookup(element=AnnotatedElement)
        parser.set_element_class_lookup(element_lookup)

        # Parse the XML file into a tree and create an rfc instance
        file = six.BytesIO(self.text)
        file.name =  os.path.join(os.path.abspath(  os.path.dirname(self.source)), os.path.basename(self.source))
        tree = lxml.etree.parse(file, parser)
        xmlrfc = XmlRfc(tree, self.default_dtd_path, nsmap=self.nsmap)

        # Evaluate processing instructions before root element
        xmlrfc._eval_pre_pi()

        # Keep seen elements in a list, to force lxml to not discard (and
        # recreate) the elements, as this would cause loss of our custom
        # state, the PI settings at the time the element was parsed
        # (in element.pis)
        xmlrfc._elements_cache = []
        # Process PIs and expand 'include' instructions
        pis = xmlrfc.pis.copy()
        for element in xmlrfc.getroot().iterdescendants():
            if element.tag is lxml.etree.PI:
                pidict = xmlrfc.parse_pi(element)
                pis = xmlrfc.pis.copy()
                if 'include' in pidict and pidict['include'] and not self.no_xinclude:
                    request = pidict['include']
                    path, originalPath = self.cachingResolver.getReferenceRequest(request,
                           # Pass the line number in XML for error bubbling
                           include=True, line_no=getattr(element, 'sourceline', 0))
                    try:
                        # Parse the xml and attach it to the tree here
                        parser = lxml.etree.XMLParser(load_dtd=False,
                                                      no_network=False,
                                                      remove_comments=remove_comments,
                                                      remove_pis=remove_pis,
                                                      remove_blank_text=True,
                                                      resolve_entities=True,
                                                      strip_cdata=strip_cdata)
                        parser.set_element_class_lookup(element_lookup)
                        # parser.resolvers.add(self.cachingResolver) --- should this be done?
                        ref_root = lxml.etree.parse(path, parser).getroot()
                        ref_root.pis = pis
                        ref_root.base = path
                        xmlrfc._elements_cache.append(ref_root)
                        for e in ref_root.iterdescendants():
                            e.pis = pis
                            e.base = path
                            xmlrfc._elements_cache.append(e)
                        parent = element.getparent()
                        parent.replace(element, ref_root)
                    except (lxml.etree.XMLSyntaxError, IOError) as e:
                        if e is lxml.etree.XMLSyntaxError:
                            log.warn('The include file at', path,
                                             'contained an XML error and was '\
                                             'not expanded:', e.msg)
                        else:
                            log.warn('Unable to load the include file at',
                                              path)
            else:
                if isinstance(element, AnnotatedElement):
                    element.pis = pis
                    xmlrfc._elements_cache.append(element)

        # Process xi:include statements

        if not self.no_xinclude:
            xmlrfc.tree.xinclude()

        # Finally, do any extra formatting on the RFC before returning
        if not self.preserve_all_white:
            xmlrfc._format_whitespace()

        return xmlrfc


class XmlRfc:
    """ Internal representation of an RFC document

        Contains an lxml.etree.ElementTree, with some additional helper
        methods to prepare the tree for output.

        Accessing the rfc tree is done by getting the root node from getroot()
    """

    pis = {}

    def __init__(self, tree, default_dtd_path, nsmap={}):
        self.default_dtd_path = default_dtd_path
        self.tree = tree
        self.nsmap = nsmap
        # Pi default values
        self.pis = {
            "artworkdelimiter":	None,
            "artworklines":	"0",
            "authorship":	"yes",
            "autobreaks":	"yes",
            "background":	"",
            "colonspace":	"no",
            "comments":		"no",
            "docmapping":	"no",
            "editing":		"no",
            #"emoticonic":	"no",
            #"footer":		Unset
            "figurecount":      "no",
            #"header":		Unset
            "inline":		"no",
            #"iprnotified":	"no",
            "linkmailto":	"yes",
            #"linefile":	Unset
            "needLines":        None,
            "multiple-initials": "no",
            #"notedraftinprogress": "yes",
            "orphanlimit":      "2",
            "private":		"",
            "refparent":	"References",
            "rfcedstyle":	"no",
            #"rfcprocack":	"no",
            "sectionorphan":    "4",
            #"slides":		"no",
            "sortrefs":		"yes",
            #"strict":		"no",
            "symrefs":		"yes",
            "tablecount":       "no",
            "text-list-symbols": "o*+-",
            "toc":		"no",
            "tocappendix":	"yes",
            "tocdepth":		"3",
            "tocindent":	"yes",
            "tocnarrow":	"yes",
            #"tocompact":	"yes",
            "tocpagebreak":     "no",
            "topblock":		"yes",
            #"typeout":		Unset
            #"useobject":	"no" ,
            "widowlimit":       "2",
        }
        # Special cases:
        self.pis["compact"] = self.pis["rfcedstyle"]
        self.pis["subcompact"] = self.pis["compact"]

    def getroot(self):
        """ Wrapper method to get the root of the XML tree"""
        return self.tree.getroot()

    def getpis(self):
        """ Returns a list of the XML processing instructions """
        return self.pis.copy()

    def validate(self, dtd_path=None, rng_path=None):
        """ Validate the document with its default dtd, or an optional one

            Return a success bool along with a list of any errors
        """
        if rng_path:
            if os.path.exists(rng_path):
                try:
                    rng = lxml.etree.parse(rng_path)
                    rng = lxml.etree.RelaxNG(rng)
                except lxml.etree.XMLSyntaxError as e:
                    log.error('Could not parse the rng file: ',
                              rng_path + '\n ', e.message)
                    return False, []
                except lxml.etree.RelaxNGParseError as e:
                    log.error('Could not parse the rng file: ',
                              rng_path + '\n ', e.error_log.last_error.message)
                    return False, []
            else:
                # Invalid path given
                log.error("RNG file does not exist ", rng_path)
                return False, []

            if rng.validate(self.tree):
                # The document was valid
                return True, []
            else:
                if len(rng.error_log) == 0:
                    return True, []
                else:
                    # The document was not valid
                    return False, rng.error_log

        # Load dtd from alternate path, if it was specified
        if dtd_path:
            if os.path.exists(dtd_path):
                try:
                    dtd = lxml.etree.DTD(dtd_path)
                except lxml.etree.DTDParseError as e:
                    # The DTD itself has errors
                    log.error('Could not parse the dtd file:',
                                      dtd_path + '\n  ', e.message)
                    return False, []
            else:
                # Invalid path given
                log.error('DTD file does not exist:', dtd_path)
                return False, []

        # Otherwise, use document's DTD declaration
        else:
            dtd = self.tree.docinfo.externalDTD

        if not dtd and self.default_dtd_path:
            # No explicit DTD filename OR declaration in document!
            log.warn('No DTD given, defaulting to', self.default_dtd_path)
            return self.validate(dtd_path=self.default_dtd_path)

        if not dtd or dtd.validate(self.getroot()):
            # The document was valid
            return True, []
        else:
            if len(dtd.error_log) == 0:
                return True, []
            else:
                # The document was not valid
                return False, dtd.error_log

    def parse_pi(self, pi):
        return utils.parse_pi(pi, self.pis)

    def _eval_pre_pi(self):
        """ Evaluate pre-document processing instructions

            This will look at all processing instructions before the root node
            for initial document settings.
        """
        # Grab processing instructions from xml tree
        element = self.tree.getroot().getprevious()
        while element is not None:
            if element.tag is lxml.etree.PI:
                self.parse_pi(element)
            element = element.getprevious()

    def _format_whitespace(self):
        utils.formatXmlWhitespace(self.getroot())
