# --------------------------------------------------
# Copyright The IETF Trust 2011, All Rights Reserved
# --------------------------------------------------

""" Module Singleton which handles output of warnings and errors to
    stdout/stderr, or alternatively to specified file paths.

    If warn_error is set, then any warnings submitted will raise a
    python exception.
"""

import sys
import os

quiet = False
verbose = False
debug = False

write_out = sys.stdout
write_err = sys.stderr


def write_on_line(*args):
    """ Writes a message without ending the line, i.e. in a loading bar """
    write_err.write(' '.join(args))
    write_err.flush()


def write(*args):
    """ Prints a message to write_out """
    write_err.write(' '.join(args))
    write_err.write('\n')


def note(*args):
    """ Call for being verbose only """
    if verbose and not quiet:
        write(*args)


def warn(*args):
    """ Prints a warning message unless quiet """
    if not quiet:
        write_err.write('WARNING: ' + ' '.join(args))
        write_err.write('\n')


def error(*args, **kwargs):
    """ This is typically called after an exception was already raised. """
    prefix = "ERROR: "
    if 'where' in kwargs:
        where = kwargs['where']
        fileName = where.base
        if fileName.startswith("file:///"):
            fileName = os.path.relpath(fileName[8:])
        elif fileName[0:6] == 'file:/':
            fileName = os.path.relpath(fileName[6:])
        prefix = "{0}:{1}: ".format(fileName, where.sourceline)
    write_err.write(prefix + u' '.join(args))
    write_err.write('\n')


def exception(message, list):
    error(message)
    if isinstance(list, Exception):
        list = [list]
    for e in list:
        attr = dict([(n, str(getattr(e, n)).replace("\n", " ")) for n in dir(e) if not n.startswith("_")])
        if attr["message"].endswith(", got "):
            attr["message"] += "nothing."
        write_err.write(" %(filename)s: Line %(line)s: %(message)s\n" % attr)
