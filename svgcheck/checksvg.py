# This source file originally came from
#
# Nevil Brownlee, U Auckland
#

# From a simple original version by Joe Hildebrand

from svgcheck import log

import re

import svgcheck.word_properties as wp

indent = 4
errorCount = 0

trace = True

bad_namespaces = []


def maybefloat(f):
    try:
        return float(f)
    except (ValueError, TypeError):
        return None


def modify_style(node):
    """
    For style properties, we want to pull it apart and then make individual attributes
    """
    log.note("modify_style check '{0}' in '{1}'".format(node.attrib['style'], node.tag))

    style_props = node.attrib['style'].rstrip(';').split(';')
    props_to_check = wp.style_properties

    for prop in style_props:
        # print("prop = %s" %  prop)
        v = prop.split(':')
        if len(v) != 2:
            log.error("Malformed field '{0}' in style attribute found. Field removed.".format(v),
                      where=node)
            continue
        p = v[0].strip()
        v = v[1].strip()  # May have leading blank
        log.note("   modify_style - p={0}  v={1}".format(p, v))
        # we will deal with the change of values later when the attribute list is processed.
        if p in props_to_check:
            log.error("Style property '{0}' promoted to attribute".format(p), where=node)
            node.attrib[p] = v
        else:
            log.error("Style property '{0}' removed".format(p), where=node)
    del node.attrib['style']


def value_ok(obj, v):
    """
    Check that the value v is a legal value for the attribute passed in
    The return value is going to be (Value OK?, Replacement value)
    v -> set of values
    obj -> attribute name
    Returns if the value is ok, and if there is a value that should be used
    to replace the value if it is not.
    """

    log.note("value_ok look for %s in %s" % (v, obj))
    # Look if the object is a real attribute, or we recursed w/ an
    # internal type name such as '<color>' (i.e. a basic_type)
    if obj in wp.properties:
        values = wp.properties[obj]
    elif obj in wp.basic_types:
        values = wp.basic_types[obj]
    elif isinstance(obj, str):
        # values to check is a string
        if obj[0] == '+':
            n = re.match(r'\d+\.\d+%?$', v)
            rv = None
            if n:
                rv = n.group()
            return (True, rv)
        # if obj[0] == '[':
        #     return check_some_props(obj, v)
        if v == obj:
            return (True, v)
        return (False, None)
    else:  # Unknown attribute
        return (False, None)

    log.note("  legal value list {0}".format(values))
    if len(values) == 0:
        # Empty tuples have nothing to check, assume it is correct
        return (True, None)

    replaceWith = None
    for val in values:
        ok_v, matched_v = value_ok(val, v)
        if ok_v:
            return (True, matched_v)
        if matched_v:
            replaceWith = matched_v

    log.note(" --- skip to end -- {0}".format(obj))
    v = v.lower()
    if obj == 'font-family':
        all = v.split(',')
        newFonts = []
        for font in ["sans-serif", "serif", "monospace"]:
            if font in all:
                newFonts.append(font)
        if len(newFonts) == 0:
            newFonts.append("sans-serif")
        return (False, ",".join(newFonts))
    if obj == '<color>':
        if v in wp.color_map:
            return (False, wp.color_map[v])

        # Heuristic conversion of color or grayscale
        # when we get here, v is a non-conforming color element
        if ('rgb(' not in v) and v[0] != '#':
            return (False, wp.color_default)
        if v[0] == '#' and len(v) == 7:
            # hexadecimal color code
            shade = int(v[1:3], 16) + int(v[3:5], 16) + int(v[5:7], 16)
        elif v[0] == '#' and len(v) == 4:
            shade = int(v[1], 16)*16 + int(v[1], 16) + int(v[2], 16)*16 + int(v[2], 16) + \
                    int(v[3], 16)*16 + int(v[3], 16)
        elif 'rgb(' in v:
            triple = v.split('(')[1].split(')')[0].split(',')
            if '%' in triple[0]:
                shade = sum([int(t.replace('%', ''))*255/100 for t in triple])
            else:
                shade = sum([int(t) for t in triple])
        else:
            shade = 0

        log.note("Color or grayscale heuristic applied to: '{0}' yields shade: '{1}'".
                 format(v, shade))
        if shade > wp.color_threshold:
            return (False, 'white')
        return (False, wp.color_default)

    return (False, replaceWith)


def strip_prefix(element, el):
    """
    Given the tag for an element, separate the namespace from the tag
    and return a tuple of the namespace and the local tag
    It will be up to the caller to determine if the namespace is acceptable
    """

    ns = None
    if element[0] == '{':
        rbp = element.rfind('}')  # Index of rightmost }
        if rbp >= 0:
            ns = element[1:rbp]
            element = element[rbp+1:]
        else:
            log.warn("Malformed namespace.  Should have errored during parsing")
    return element, ns  # return tag, namespace


def check(el, depth=0):
    """
    Walk the current tree checking to see if all elements pass muster
    relative to RFC 7996 the RFC Tiny SVG document

    Return False if the element is to be removed from tree when
    writing it back out
    """
    global errorCount

    log.note("%s tag = %s" % (' ' * (depth*indent), el.tag))

    # Check that the namespace is one of the pre-approved ones
    # ElementTree prefixes elements with default namespace in braces

    element, ns = strip_prefix(el.tag, el)  # name of element

    # namespace for elements must be either empty or svg
    if ns is not None and ns not in wp.svg_urls:
        log.warn("Element '{0}' in namespace '{1}' is not allowed".format(element, ns),
                 where=el)
        return False  # Remove this el

    # Is the element in the list of legal elements?
    log.note("%s element % s: %s" % (' ' * (depth*indent), element, el.attrib))
    if element not in wp.elements:
        errorCount += 1
        log.warn("Element '{0}' not allowed".format(element), where=el)
        return False  # Remove this el

    elementAttributes = wp.elements[element]  # Allowed attributes for element

    # do a re-write of style into individual elements
    if 'style' in el.attrib:
        modify_style(el)

    attribs_to_remove = []  # Can't remove them inside the iteration!
    for nsAttrib, val in el.attrib.items():
        # validate that the namespace of the element is known and ok
        attr, ns = strip_prefix(nsAttrib, el)
        log.note("%s attr %s = %s (ns = %s)" % (
                ' ' * (depth*indent), attr, val, ns))
        if ns is not None and ns not in wp.svg_urls:
            if ns not in wp.xmlns_urls:
                log.warn("Element '{0}' does not allow attributes with namespace '{1}'".
                         format(element, ns), where=el)
                attribs_to_remove.append(nsAttrib)
            continue

        # look to see if the attribute is either an attribute for a specific
        # element or is an attribute generically for all properties
        if (attr not in elementAttributes) and (attr not in wp.properties):
            errorCount += 1
            log.warn("The element '{0}' does not allow the attribute '{1}',"
                     " attribute to be removed.".format(element, attr),
                     where=el)
            attribs_to_remove.append(nsAttrib)

        # Now check if the attribute is a generic property
        elif (attr in wp.properties):
            vals = wp.properties[attr]
            # log.note("vals = " + vals +  "<<<<<")

            #  Do method #1 of checking if the value is legal - not currently used.
            if vals and vals[0] == '[' and False:
                # ok, new_val = check_some_props(attr, val, depth)
                # if not ok:
                #    el.attrib[attr] = new_val[1:]
                pass
            else:
                ok, new_val = value_ok(attr, val)
                if vals and not ok:
                    errorCount += 1
                    if new_val is not None:
                        el.attrib[attr] = new_val
                        log.warn("The attribute '{1}' does not allow the value '{0}',"
                                 " replaced with '{2}'".format(val, attr, new_val), where=el)
                    else:
                        attribs_to_remove.append(nsAttrib)
                        log.warn("The attribute '{1}' does not allow the value '{0}',"
                                 " attribute to be removed".format(val, attr), where=el)

    for attrib in attribs_to_remove:
        del el.attrib[attrib]

    # Need to have a viewBox on the root
    if (depth == 0):
        if el.get("viewBox"):
            pass
        else:
            log.warn("The attribute viewBox is required on the root svg element", where=el)
            svgw = maybefloat(el.get('width'))
            svgh = maybefloat(el.get('height'))
            try:
                if svgw and svgh:
                    newValue = '0 0 %s %s' % (svgw, svgh)
                    log.warn("Trying to put in the attribute with value '{0}'".
                             format(newValue), where=el)
                    el.set('viewBox', newValue)
            except ValueError as e:
                log.error("Error when calculating SVG size: %s" % e, where=el)

    els_to_rm = []  # Can't remove them inside the iteration!
    if element in wp.element_children:
        allowed_children = wp.element_children[element]
    else:
        allowed_children = []

    for child in el:
        log.note("%schild, tag = %s" % (' ' * (depth*indent), child.tag))
        if not isinstance(child.tag, str):
            continue
        ch_tag, ns = strip_prefix(child.tag, el)
        if ns not in wp.svg_urls:
            log.warn("The namespace {0} is not permitted for svg elements.".format(ns),
                     where=child)
            els_to_rm.append(child)
            continue

        if ch_tag not in allowed_children:
            log.warn("The element '{0}' is not allowed as a child of '{1}'".
                     format(ch_tag, element), where=child)
            els_to_rm.append(child)
        elif not check(child, depth+1):
            els_to_rm.append(child)

    if len(els_to_rm) != 0:
        for child in els_to_rm:
            el.remove(child)
    return True  # OK


def checkTree(tree):
    """
    Process the XML tree.  There are two cases to be dealt with
    1. This is a simple svg at the root - can be either the real namespace or
       an empty namespace
    2. This is an rfc tree - and we should only look for real namespaces, but
       there may be more than one thing to look for.
    """
    global errorCount

    errorCount = 0
    element = tree.getroot().tag
    if element[0] == '{':
        element = element[element.rfind('}')+1:]
    if element == 'svg':
        check(tree.getroot(), 0)
    else:
        # Locate all of the svg elements that we need to check

        svgPaths = tree.getroot().xpath("//x:svg", namespaces={'x': 'http://www.w3.org/2000/svg'})

        for path in svgPaths:
            if len(svgPaths) > 1:
                log.note("Checking svg element at line {0} in file {1}".format(1, "file"))
            check(path, 0)

    return errorCount == 0
