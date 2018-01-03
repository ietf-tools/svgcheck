#!/usr/bin/env python

# Thu, 24 Sep 15 (NZST)
# Sat,  7 Jun 14 (NZST)
#
# check-svg.py:  ./check-svg.py -n diagram.svg
#                ./check-svy.py --help  # to see options info
#
# Nevil Brownlee, U Auckland

# From a simple original version by Joe Hildebrand

from rfctools_common import log

# '''  # ElementTree doesn't have nsmap
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
# '''
# from lxml import etree as ET

import getopt
import sys
import re

import word_properties as wp

indent = 4
current_file = None
errorCount = 0

trace = True

bad_namespaces = []


def check_some_props(attr, val, depth):
    """
    This function is not currently being used.
    For [style] properties
    """

    vals = wp.properties[attr]
    props_to_check = wp.property_lists[vals]
    new_val = ''
    ok = True
    old_props = val.rstrip(';').split(';')
    # print("old_props = %s" % old_props)
    for prop in old_props:
        # print("prop = %s" %  prop)
        p, v = prop.split(':')
        v = v.strip()  # May have leading blank
        if p in props_to_check:
            allowed_vals = wp.properties[p]
            # print("$$$ p=%s, allowed_vals=%s." % (p, allowed_vals))
            allowed = value_ok(v, p)
            if not allowed:
                warn("??? %s attribute: value '%s' not valid for '%s'" % (
                    attr, v, p), depth)
                ok = False
        else:
            new_val += ';' + prop
    return (ok, new_val)


def value_ok(v, obj):
    """
    Check that the value v is a legal value for the attribute passed in
    The return value is going to be (Value OK?, Replacement value)
    Returns if the value is ok, and if there is a value that should be used
    to replace the value if it is not.
    """

    log.note("value_ok(%s, %s)" % (v, obj))
    # Look if the object is a real attribute, or we recursed w/ an
    # internal type name such as '<color>' (i.e. a basic_type)
    if obj not in wp.properties:
        if obj not in wp.basic_types:
            return (False, None)

        values = wp.basic_types[obj]

        # Integers must be ints, but have no default
        if values == '+':  # Integer
            n = re.match(r'\d+$', v)
            return (n, None)
    else:
        values = wp.properties[obj]

    # values could be a string or an array of values
    if isinstance(values, str):  # str) in python 3
        if values[0] == '<' or values[0] == '+':
            log.warn(". . . values = >%s<" % values)
            return value_ok(False, None)
    else:
        for val in values:
            if val[0] == '<':
                return value_ok(v, val)
            if v == val:
                return (True, None)
            elif val == '#':  # RGB value
                lv = v.lower()
                if lv[0] == '#':  # rrggbb  hex
                    if len(lv) == 7:
                        return (lv[3:5] == lv[1:3] and lv[5:7] == lv[1:3] and
                                (lv[1:3] == '00' or lv[1:3] == 'ff'), None)
                    if len(lv) == 4:
                        return (lv[2] == lv[1] and lv[3] == lv[1] and
                                (lv[1] == '0' or lv[1] == 'f'), None)
                    return (False, None)
                elif lv.find('rgb') == 0:  # integers
                    rgb = re.search(r'\((\d+),(\d+),(\d+)\)', lv)
                    if rgb:
                        return ((rgb.group(2) == rgb.group(1) and
                                 rgb.group(3) == rgb.group(1)) and
                                (rgb.group(1) == '0' or rgb.group(1) == 256), None)
                    return (False, None)
        v = v.lower()
        if obj == 'font-family':
            if v.find('sans') >= 0:
                return (False, 'sans-serif')
        if obj == '<color>':
            return (False, wp.color_default)
        return (False, None)


def strip_prefix(element, el):  # Remove {namespace} prefix
    global bad_namespaces
    ns_ok = True
    if element[0] == '{':
        rbp = element.rfind('}')  # Index of rightmost }
        if rbp >= 0:
            ns = element[1:rbp]
            if ns not in wp.xmlns_urls:
                if ns not in bad_namespaces:
                    bad_namespaces.append(ns)
                    log.error("Namespace {0} is not permitted".format(ns), where=el)
                ns_ok = False
            element = element[rbp+1:]
    return element, ns_ok  # return ns = False if it's not allowed


def check(el, depth=0):
    """
    Walk the current tree checking to see if all elements pass muster
    relative to RFC 7996 the RFC Tiny SVG document

    Return False if the element is to be removed from tree when
    writing it back out
    """
    global new_file

    log.note("%s tag = %s" % (' ' * (depth*indent), el.tag))

    # Check that the namespace is one of the pre-approved ones
    # ElementTree prefixes elements with default namespace in braces
    element, ns_ok = strip_prefix(el.tag, el)  # name of element
    if not ns_ok:
        return False  # Remove this el

    # Is the element in the list of legal elements?
    log.note("%s element % s: %s" % (' ' * (depth*indent), element, el.attrib))
    if element not in wp.elements:
        log.error("Element '{0}' not allowed".format(element), where=el)
        return False  # Remove this el

    elementAttributes = wp.elements[element]  # Allowed attributes for element

    attribs_to_remove = []  # Can't remove them inside the iteration!
    for nsAttrib, val in el.attrib.items():
        # validate that the namespace of the element is known and ok
        attr, ns_ok = strip_prefix(nsAttrib, el)
        log.note("%s attr %s = %s (ns_ok = %s)" % (
                ' ' * (depth*indent), attr, val, ns_ok))
        if not ns_ok:
            attribs_to_remove.append(attr)
            continue

        # look to see if the attribute is either an attribute for a specific
        # element or is an attribute generically for all properties
        if (attr not in elementAttributes) and (attr not in wp.properties):
            log.error("Element '{0}' does not allow attribute '{1}'".
                      format(element, attr), where=el)
            attribs_to_remove.append(nsAttrib)

        # Now check if the attribute is a generic property
        elif (attr in wp.properties):
            vals = wp.properties[attr]
            # log.note("vals = " + vals +  "<<<<<")

            #  Do method #1 of checking if the value is legal - not currently used.
            if vals and vals[0] == '[':
                ok, new_val = check_some_props(attr, val, depth)
                if not ok:
                    el.attrib[attr] = new_val[1:]

            else:
                ok, new_val = value_ok(val, attr)
                if vals and not ok:
                    log.error("{0} not allowed as value for {1}".format(val, attr), where=el)
                    if new_val is not None:
                        el.attrib[attr] = new_val
                    else:
                        attribs_to_remove.append(nsAttrib)

    for attrib in attribs_to_remove:
        del el.attrib[attrib]

    els_to_rm = []  # Can't remove them inside the iteration!
    for child in el:
        log.note("%schild, tag = %s" % (' ' * (depth*indent), child.tag))
        if not check(child, depth+1):
            els_to_rm.append(child)
    if len(els_to_rm) != 0:
        for child in els_to_rm:
            el.remove(child)
    return True  # OK


def remove_namespace(doc, namespace):
    # From  http://stackoverflow.com/questions/18159221/
    #   remove-namespace-and-prefix-from-xml-in-python-using-lxml
    ns = u'{%s}' % namespace
    nsl = len(ns)
    for elem in doc.getiterator():
        if elem.tag.startswith(ns):
            print("elem.tag before=%s," % elem.tag)
            elem.tag = elem.tag[nsl:]
            print("after=%s." % elem.tag)


def checkFile(fn):
    global current_file, root
    current_file = fn
    print("Starting %s" % current_file)
    tree = ET.parse(fn)
    root = tree.getroot()
    # print("root.attrib=%s, test -> %d" % (root.attrib, "xmlns" in root.attrib))
    #    # attrib list doesn't have includes "xmlns", even though it's there
    # print("root.tag=%s" % root.tag)
    no_ns = root.tag.find("{") < 0
    # print("no_ns = %s" % no_ns)

    ET.register_namespace("", "http://www.w3.org/2000/svg")
    # Stops tree.write() from prefixing above with "ns0"
    check(root, 0)
    print("bad_namespaces = %s" % bad_namespaces)
    if trace and len(bad_namespaces) != 0:
        print("bad_namespaces = %s" % bad_namespaces)
    if new_file:
        sp = fn.rfind('.svg')
        if sp+3 != len(fn)-1:  # Indeces of last chars
            print("filename doesn't end in '.svg' (%d, %d)" % (sp, len(fn)))
        else:
            if no_ns:
                root.attrib["xmlns"] = "http://www.w3.org/2000/svg"
            for ns in bad_namespaces:
                remove_namespace(root, ns)
            new_fn = fn.replace(".svg", ".new.svg")
            print("writing to %s" % (new_fn))
            tree.write(new_fn)
