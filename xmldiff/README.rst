Create a difference on two RFC XML files
========================================


This program takes two XML files containing SVG or RFC documents and creates an HTML
file which shows the differences between the two documents.

The `RFC Editor`_ is in the process of changing the canonical input format of
Internet-Draft_ and RFC_ documents.  Further information on the process can be found
on the RFC Editor at the `RFC Editor`_ site.

.. _Internet-Draft: https://en.wikipedia.org/wiki/Internet_Draft
.. _RFC: https://en.wikipedia.org/wiki/Request_for_Comments
.. _RFC Editor: https://www.rfc-editor.org

Usage
=====

rfc-xmldiff accepts a pair of XML documents as input and outputs an HTML document.

**Basic Usage**: ``rfc-xmldiff [options] SOURCE1 SOURCE2``

**Options**

   The following parameters affect how rfc-xmldiff behaves, however none are required.
   
    ================= ========================= =================================================== 
     Short             Long                      Description                                        
    ================= ========================= =================================================== 
     ``-C``            ``--clear-cache``         purge the cache and exit                           
     ``-h``            ``--help``                show the help message and exit                     
     ``-N``            ``--no-network``          don't use the network to resolve references        
     ``-q``            ``--quiet``               don't print anything                               
     ``-r``            ``--raw``                 don't use the xml2rfc vocabulary when matching     
     ``-v``            ``--verbose``             print extra information                            
     ``-V``            ``--version``             display the version number and exit                
     ``-X``            ``--no-xinclude``         don't resolve xi:include elements                  
     ``-o FILENAME``   ``--out=FILENAME``        specify an output filename                         
     ``-t FILENAME``   ``--template=FILENAME``   specify HTML template filename
     ``-D``            ``--no-defaults``         don't load attribute defaults from the dtd
     .                 ``--resource-url=URL``    specify the URL for resources in the template      
    ================= ========================= =================================================== 

Templates
=========

Two template files are installed with the package:

    * single.html - provides just the XML difference between the two files.
    * base.html - provides three columns containing the left source files, the XML difference and the right source files.   Uses color to highlight changes. This is the default template.
    * wdiff.html - provides three columns containing the left source files, the XML difference and the right source files.  Uses color and strike throughs to highlight changes.

For new template files, the following variables are define:

   * title - provides a default window title
   * body - contains the XML difference HTML
   * leftSourceNames - the list of all input files for the left sources
   * leftFile - contains the left source files
   * rigthSourceNames - the list of all input files for the right sources
   * rightFile - contains the right source files
   * resource_dir - contains the URL to find the resources.  This defaults to the Template directory of the package.
   * allScript - contains the contents of resize.js so the resulting html file is self contained.
    
Dependencies
============

rfc-xmldiff depends on the following packages:

* lxml_ *(>= 4.1.1)*
* requests_ *(>= 2.5.0)*
* `rfctools_common`_ *(>= 0.5.10)*
* cffi_ *(>= 1.0.0)*

.. _lxml: http://lxml.de
.. _requests: http://docs.python-requests.org
.. _rfctools_common: https://pypi.python.org/pypi/pip
.. _cffi: https://pypi.python.org/pypi/pip

