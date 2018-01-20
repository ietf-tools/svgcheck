Perform Validation checks on Internet-Drafts
============================================

There are a number of tasks that need to be performed when an Internet-Draft_ is
begin process to create an RFC_. This tool performs a subset of those actions.
The actions performed are:

- Validate the file is well formed XML and that it conforms to the XML2RFC Version 3
  schema as defined in RFC 7991_.
- Verify that embedded XML stanzas are well formed.
- Verify that embedded ABNF is complete and well formed.
- Identify misspelled words.
- Detect duplicate words.

The tool can be used either in an interactive mode or in batch mode.

.. _Internet-Draft: https://en.wikipedia.org/wiki/Internet_Draft
.. _RFC: https://en.wikipedia.org/wiki/Request_for_Comments
.. _RFC 7991: https://tools.ietf.org/html/rfc7991
