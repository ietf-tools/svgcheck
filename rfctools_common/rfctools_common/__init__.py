# Static values
__version__  = '0.5.3'
NAME         = 'rfctools_common'
VERSION      = [ int(i) if i.isdigit() else i for i in __version__.split('.') ]

from rfctools_common.parser import  XmlRfcError, CachingResolver, XmlRfcParser, XmlRfc

__all__ = ['XmlRfcError', 'CachingResolver', 'XmlRfcParser', 'XmlRfc',
           ]

