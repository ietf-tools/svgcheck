# --------------------------------------------------
# Copyright The IETF Trust 2011-2019, All Rights Reserved
# --------------------------------------------------

""" Module Singleton which handles output of warnings and errors to
    stdout/stderr, or alternatively to specified file paths.

    If warn_error is set, then any warnings submitted will raise a
    python exception.
"""

import sys
import os
import io

quiet = False
verbose = False
debug = False

write_err = sys.stderr


def info(*args, **kwargs):
    """ Prints a warning message unless quiet """
    prefix = "INFO: "
    if 'where' in kwargs:
        where = kwargs['where']
        fileName = where.base
        if fileName.startswith("file:///"):
            fileName = os.path.relpath(fileName[8:])
        elif fileName[0:6] == 'file:/':
            fileName = os.path.relpath(fileName[6:])
        elif fileName[0:7] == 'http://' or fileName[0:8] == 'https://':
            pass
        else:
            fileName = os.path.relpath(fileName)
        prefix = "{0}:{1}: ".format(fileName, where.sourceline)
    write_err.write(prefix + ' '.join(args))
    write_err.write('\n')
    write_err.flush()


def note(*args):
    """ Call for being verbose only """
    if verbose and not quiet:
        write_err.write(' '.join(args))
        write_err.write('\n')


def warn(*args, **kwargs):
    """ Prints a warning message unless quiet """
    if not quiet:
        prefix = "WARNING: "
        if 'where' in kwargs:
            where = kwargs['where']
            fileName = where.base
            if fileName.startswith("file:///"):
                fileName = os.path.relpath(fileName[8:])
            elif fileName[0:6] == 'file:/':
                fileName = os.path.relpath(fileName[6:])
            elif fileName[0:7] == 'http://' or fileName[0:8] == 'https://':
                pass
            else:
                fileName = os.path.relpath(fileName)
            prefix = "{0}:{1}: ".format(fileName, where.sourceline)
        write_err.write(prefix + u' '.join(args))
        write_err.write('\n')
        write_err.flush()


def error(*args, **kwargs):
    """ This is typically called after an exception was already raised. """
    prefix = "ERROR: "
    if 'where' in kwargs:
        where = kwargs['where']
        fileName = make_relative(where.base)
        prefix = "{0}:{1}: ".format(fileName, where.sourceline)
    if 'file' in kwargs:
        fileName = make_relative(kwargs['file'])
        prefix = "{0}:{1}: ".format(fileName, kwargs['line'])
    if 'additional' in kwargs:
        prefix = ' ' * kwargs['additional']

    write_err.write(prefix + ' '.join(args))
    write_err.write('\n')
    write_err.flush()


def exception(message, list):
    error(message)
    if isinstance(list, Exception):
        list = [list]
    for e in list:
        attr = dict([(n, str(getattr(e, n)).replace("\n", " ")) for n in dir(e)
                     if not n.startswith("_")])
        if 'message' in attr:
            if attr["message"].endswith(", got "):
                attr["message"] += "nothing."
        else:
            attr['message'] = '-- none --'
        if 'filename' in attr:
            attr["filename"] = make_relative(attr["filename"])
        else:
            attr['filename'] = 'unknown'
        if 'line' not in attr:
            attr['line'] = -1
        write_err.write(" %(filename)s: Line %(line)s: %(message)s\n" % attr)


def exception_lines(message, list):
    if isinstance(list, Exception):
        list = [list]
    for e in list:
        attr = dict([(n, str(getattr(e, n)).replace("\n", " ")) for n in dir(e)
                     if not n.startswith("_")])
        if attr["message"].endswith(", got "):
            attr["message"] += "nothing."
        attr["filename"] = make_relative(attr["filename"])
        write_err.write(" %(filename)s: Line %(line)s: %(message)s\n" % attr)


def make_relative(fileName):
    if fileName.startswith("file:///"):
        fileName = os.path.relpath(fileName[8:])
    elif fileName[0:6] == 'file:/':
        fileName = os.path.relpath(fileName[6:])
    else:
        fileName = os.path.relpath(fileName)
    return fileName
