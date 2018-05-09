Check SVG against RFC schema
============================

This program takes an XML file containing an SVG or an RFC document.  It then compares
all of the SVG elements with the schema defined in the document with `RFC 7996 bis`_.
The program has the option
of modifying and writing out a version of the input that passes the defined schema.

The `RFC Editor`_ is in the process of changing the canonical input format of
Internet-Draft_ and RFC_ docuemnts.  As part of this process, the ability to create
artwork which is not ASCII text is being introduced.  This is being done with SVG.
However, the full set of SVG does not match with the archival nature of RFCs so
a subset of the SVG specification is being defined by the RFC Editor that eliminates
many capabilities such as animation.  Additionally, there is a requirement that
the images have the widest possible usage both by printers, monochrome displays and
individuals with visual disabilities.  Further information on the process can be found
on the RFC Editor at the `RFC Editor`_ site.

.. _Internet-Draft: https://en.wikipedia.org/wiki/Internet_Draft
.. _RFC: https://en.wikipedia.org/wiki/Request_for_Comments
.. _RFC 7996 bis: https://datatracker.ietf.org/doc/draft-7996-bis
.. _RFC Editor: https://www.rfc-editor.org

Usage
=====

svgcheck accepts a single XML document as input and optionally outputs a modified version of
the document.

**Basic Usage**: ``svgcheck [options] SOURCE``

**Options**
   The following parameters affect how svgcheck behaves, however none are required.

    ===============  ======================= ==================================================
    Short            Long                    Description
    ===============  ======================= ==================================================
    ``-C``           ``--clear-cache``       purge the cache and exit
    ``-h``           ``--help``              show the help message and exit
    ``-N``           ``--no-network``        don't use the network to resolve references
    ``-q``           ``--quiet``             dont print anything
    ``-r``           ``--repair``            repair the SVG so it meets RFC 7966
    ``-v``           ``--verbose``           print extra information
    ``-V``           ``--version``           display the version number and exit
    ``-X``           ``--no-xinclude``       don't resolve xi:include elements

    ``-d RNG``       ``--rng=RNG``           specify an alternate RNG file
    ``-o FILENAME``  ``--out=FILENAME``      specify an output filename
    ===============  ======================= ==================================================

Dependencies
============

svgcheck depends on the following packages:

* lxml_ *(>= 4.1.1)*
* requests_ *(>= 2.5.0)*
* `rfctools_common`_ *(>= 0.5.3)*

.. _lxml: http://lxml.de
.. _requests: http://docs.python-requests.org
.. _rfctools_common: https://pypi.python.org/pypi/pip

