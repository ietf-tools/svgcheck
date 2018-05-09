import lxml.etree
from rfctools_common.parser import XmlRfc
from rfctools_common import log
import math
import sys
import difflib
import six
from lxml.html import builder as E
from xmldiff.EditItem import EditItem
# from xmldiff.zzs import EditItem

try:
    import debug
    assert debug
except ImportError:
    pass


TextElements = [
    "bcp14", "br", "cref", "em", "eref", "iref", "strong", "relref", "sub",
    "sup", "tt", "xref", "vspace"
]

V2NonTextElements = [
    "list", "figure"
]

tagMatching = {
    "c": {"td"},
    "dd": {"t"},
    "dl": {"list"},
    "li": {"t"},
    "list": {"dl", "ol", "ul"},
    "ol": {"list"},
    "t": {"dd", "li"},
    "table": {"texttable"},
    "td": {"c"},
    "texttable": {"table"},
    "th": {"ttcol"},
    "ttcol": {"th"},
    "ul": {"list"},
}

PreserveSpace = ['artwork', 'sourcecode']

diffCount = 0
if six.PY2:
    nbsp = unichr(0xa0)
else:
    nbsp = chr(0xa0)


def ChangeTagMatching(newMatching):
    global tagMatching

    tagMatching = newMatching


def BuildDiffTree(xmlNode, options):
    """ Build the Diff tree from the xml tree """

    global diffCount

    if not isinstance(xmlNode, lxml.etree._ElementTree):
        sys.exit(2, "bad parameter")

    #  We have two problems here - the first is that lxml does
    #  not bother keeping the root elements as separate things
    #  so life is a pain

    diffCount = 0
    root = DiffDocument(xmlNode)

    # Grab nodes before the root
    element = xmlNode.getroot().getprevious()
    while element is not None:
        if element.tag is lxml.etree.PI:
            root.children.insert(0, DiffPI(element, root))

        element = element.getprevious()

    # Now process the root element itself
    root.children.append(root.createNode(xmlNode.getroot(), root))

    # Now process any elements after to root element

    element = xmlNode.getroot().getnext()
    while element is not None:
        if element.tag is lxml.etree.PI:
            root.children.append(DiffPI(element, root))

        element = element.getnext()

    if options.debug:
        print("Number of diff nodes is {0}".format(diffCount))

    return root

# Control how elements are converted from a tree to a pargaraph.
# The values here mean:
# 1 - This is always just converted to a paragraph.
# 2 - These are v3 elements which can be either a paragraph or
#     a tree (i.e. have other items inside which are paragraphs)
# 3 - These are v2 elements which may not be paragraphs
# 4 - These are v3 element which are paragraphs, but v2 elements
#     which may not be paragraphs.
#
# We ignore those elements which can only simple text and do not
# treat them as paragarphs


ParagraphMarkers = {
    'annotation': 1,
    'artwork': 2,  # need to deal with perserveSpace
    'blockquote': 2,
    'c': 3,
    'dd': 2,
    'dt': 1,
    'li': 1,
    'refcontent': 1,
    'sourcecode': 1,  # need to deal with perserveSpace
    't': 4,
    'td': 2,
    'th': 2,
    'ttcol': 3,
    '{http://relaxng.org/ns/structure/1.0}desc': 1,
    '{http://relaxng.org/ns/structure/1.0}svgTitle': 1,
    '{http://relaxng.org/ns/structure/1.0}a': 1,
    '{http://relaxng.org/ns/structure/1.0}text': 1,
    '{http://relaxng.org/ns/structure/1.0}textArea': 1,
    '{http://relaxng.org/ns/structure/1.0}tspan': 1
    }


def AddParagraphs(root):
    if not isinstance(root, DiffElement):
        for c in root.children:
            AddParagraphs(c)
        return root
    if root.xml.tag in ParagraphMarkers:
        if ParagraphMarkers[root.xml.tag] == 1 or \
           ParagraphMarkers[root.xml.tag] == 3:
            p = DiffParagraph(root.xml, root)
            p.children = root.children
            root.children = [p]
            return root
        elif ParagraphMarkers[root.xml.tag] == 2:
            newChildren = []
            p = DiffParagraph(root.xml, root)
            for child in root.children:
                if isinstance(child, DiffComment):
                    if len(p.children) > 0:
                        newChildren.append(p)
                        p = DiffParagraph(root.xml, root)
                    newChildren.append(child)
                elif not isinstance(child, DiffElement):
                    p.children.append(child)
                elif child.xml.tag in TextElements:
                    p.children.append(child)
                else:
                    if len(p.children) > 0:
                        newChildren.append(p)
                        p = DiffParagraph(root.xml, root)
                    newChildren.append(child)
            if len(p.children) > 0:
                newChildren.append(p)
            root.children = newChildren
        elif ParagraphMarkers[root.xml.tag] == 4:
            newChildren = []
            p = DiffParagraph(root.xml, root)
            for child in root.children:
                if isinstance(child, DiffComment):
                    if len(p.children) > 0:
                        newChildren.append(p)
                        p = DiffParagraph(root.xml, root)
                    newChildren.append(child)
                elif not isinstance(child, DiffElement):
                    p.children.append(child)
                elif child.xml.tag not in V2NonTextElements:
                    p.children.append(child)
                else:
                    if len(p.children) > 0:
                        newChildren.append(p)
                        p = DiffParagraph(root.xml, root)
                    newChildren.append(child)
            if len(p.children) > 0:
                newChildren.append(p)
            root.children = newChildren

    for c in root.children:
        AddParagraphs(c)
    return root


def DecorateSourceFile(diffRoot, sourceLines):
    diffRoot.decorateSource(sourceLines)


class DiffRoot(object):
    """ Root of the diff objects. """

    def __init__(self, xmlNode, parent):
        global diffCount

        self.xml = xmlNode
        self.children = []
        self.deleted = False
        self.inserted = False
        self.matchNode = None
        self.parent = parent
        diffCount += 1
        self.index = diffCount
        self.deleteTree = False
        self.preserve = False

    def ToString(self):
        node = E.DIV()
        node.text = "Need to override something"
        return node

    def toText(self):
        return lxml.etree.tostring(self.xml)  # with_tail=False

    def ToHtml(self, parent):
        node = E.LI()
        node.text = "Need to override something"
        parent.append(node)

    @staticmethod
    def get_children(n):
        return n.children

    @staticmethod
    def InsertCost(left):
        item = EditItem()
        item.setOperation(EditItem.OP_INSERT, None, left)
        if isinstance(left, DiffElement) or isinstance(left, DiffComment):
            item.cost = 10
        else:
            item.cost = 1
        return item

    @staticmethod
    def DeleteCost(left):
        item = EditItem()
        item.setOperation(EditItem.OP_DELETE, left, None)
        item.cost = left.deleteCost()
        return item

    def deleteCost(self):
        """ Compute the deletion cost of a node
            The deletion cost for an element needs to be higher
            that that for text so that doing a rename on texts
            is the preferred operation
        """
        if isinstance(self, DiffElement) or isinstance(self, DiffComment):
            cost = 10
        else:
            cost = 1
        return cost

    @staticmethod
    def UpdateCost(left, right):
        #  If the types are not the same, then the cost is extremely high
        if type(left) is not type(right):
            item = EditItem()
            item.setOperation(EditItem.OP_RENAME, left, right)
            item.cost = 100000
            return item
        return left.updateCost(right)

    def updateCost(self, right):
        return 100

    def _serialize(self, element):
        if sys.version > '3':
            return lxml.html.tostring(element, pretty_print=True, method='html',
                                      encoding='ascii').decode('ascii')
        else:
            return lxml.html.tostring(element, pretty_print=True, method='html',
                                      encoding='ascii').decode('ascii')

    def markInsertTrees(self):
        insertTree = True
        for child in self.children:
            insertTree &= child.markInsertTrees()
        insertTree &= (self.matchNode is None)
        self.insertTree = insertTree
        return insertTree

    def markDeleteTrees(self):
        deleteTree = True
        for child in self.children:
            deleteTree &= child.markDeleteTrees()
        deleteTree &= (self.matchNode is None)
        self.deleteTree = deleteTree
        return deleteTree

    def createNode(self, xml, parent):
        if xml.tag is lxml.etree.PI:
            return DiffPI(xml, parent)
        if xml.tag is lxml.etree.Comment:
            return DiffComment(xml, parent)
        textTest = "foo bar" + xml.tag
        return DiffElement(xml, parent)

    def getPredecessor(self, searchNode):
        prevSib = None
        for child in self.children:
            if searchNode.isMatchNode(child):
                return prevSib
            prevSib = child
        return None

    def getSuccessor(self, searchNode):
        found = False
        for child in self.children:
            if found:
                return child
            if searchNode.isMatchNode(child):
                found = True

        return None

    def isMatchNode(self, other):
        if self == other:
            return True
        if self.deleted:
            if len(self.children) != 1:
                return False
            return self.children[0].isMatchNode(other)
        if other.deleted:
            if len(other.children) != 1:
                return False
            return self.isMatchNode(other.children[0])
        return False

    def insertAfter(self, siblingNode, newNode):
        """ Insert newNode after siblingNode """
        i = 0
        for child in siblingNode.parent.children:
            if siblingNode.isMatchNode(child):
                break
            i += 1
        if i == len(siblingNode.parent.children):
            log.error("ICE: insertAfter failed to find node.")
            siblingNode.parent.children.append(newNode)
        else:
            siblingNode.parent.children.insert(i+1, newNode)
        newNode.parent = siblingNode.parent

    def insertBefore(self, siblingNode, newNode):
        i = 0
        for child in siblingNode.parent.children:
            if siblingNode.isMatchNode(child):
                break
            i += 1
        if i == len(siblingNode.parent.children):
            # assert false
            log.error("ICE: insertBefore failed to find node.")
            siblingNode.parent.children.append(newNode)
        else:
            siblingNode.parent.children.insert(i, newNode)
        newNode.parent = siblingNode.parent

    def fixPreserveSpace(self, node, text):
        if self.preserve:
            text = text.splitlines(1)
            n = None
            for line in text:
                if node.text is None:
                    node.text = line.replace(' ', nbsp)
                else:
                    n.tail = line.replace(' ', nbsp)
                if line[-1:] == '\n':
                    n = E.BR()
                    node.append(n)
        else:
            node.text = text

    def diffTextToHtml(self, leftText, rightText, node):
        if self.preserve:
            n = E.SPAN()
            n.attrib['class'] = 'artwork'
            node.append(n)
            node = n
        if not rightText:
            if not leftText:
                return
            n = E.SPAN()
            n.attrib["class"] = 'left'
            self.fixPreserveSpace(n, leftText)
            node.append(n)
        elif not leftText:
            n = E.SPAN()
            n.attrib['class'] = 'right'
            self.fixPreserveSpace(n, rightText)
            node.append(n)
        else:
            differ = difflib.SequenceMatcher(None, leftText, rightText)
            for tag, i1, i2, j1, j2 in differ.get_opcodes():
                if tag == 'equal':
                    n = E.SPAN()
                    self.fixPreserveSpace(n, leftText[i1:i2])
                    node.append(n)
                elif tag == 'delete':
                    n = E.SPAN()
                    n.attrib['class'] = 'left'
                    self.fixPreserveSpace(n, leftText[i1:i2])
                    node.append(n)
                elif tag == 'insert':
                    n = E.SPAN()
                    n.attrib['class'] = 'right'
                    self.fixPreserveSpace(n, rightText[j1:j2])
                    node.append(n)
                else:
                    n = E.SPAN()
                    n.attrib['class'] = 'left'
                    self.fixPreserveSpace(n, leftText[i1:i2])
                    node.append(n)
                    n = E.SPAN()
                    n.attrib['class'] = 'right'
                    self.fixPreserveSpace(n, rightText[j1:j2])
                    node.append(n)


class DiffDocument(DiffRoot):
    """ Represent the XML document.  We want to have a common
        node type that is always at the root for comparisions
    """

    def __init__(self, xmlNode):
        DiffRoot.__init__(self, xmlNode, None)

    def ToString(self):
        result = E.DIV()
        result.attrib['class'] = 'center'

        ul = E.UL()
        result.append(ul)
        ul.attrib['class'] = 'mktree'
        ul.attrib['id'] = 'diffRoot'

        #  Insert xml declarations

        n = E.LI()
        n.attrib['whereLeft'] = "L0_0"
        n.attrib['whereRight'] = "R0_0"
        leftText = '<?xml version="{0}" encoding="{1}"?>'.format(self.xml.docinfo.xml_version,
                                                                 self.xml.docinfo.encoding)
        rightText = '<?xml version="{0}" encoding="{1}"?>'. \
            format(self.matchNode.xml.docinfo.xml_version,
                   self.matchNode.xml.docinfo.encoding)
        self.diffTextToHtml(leftText, rightText, n)
        ul.append(n)

        # Insert DTD declaration if one exists
        n = E.LI()
        if self.xml.docinfo.doctype or self.matchNode.xml.docinfo.doctype:
            self.diffTextToHtml(self.xml.docinfo.doctype, self.matchNode.xml.docinfo.doctype, n)
            ul.append(n)

        # now put all of the children into HTML

        for child in self.children:
            child.ToHtml(ul)

        return self._serialize(result)

    def updateCost(self, right):
        return 0

    def decorateSource(self, sourceLines):
        for child in self.children:
            child.decorateSource(sourceLines)

    def applyEdits(self, editList):
        newEdits = []
        for edit in editList:
            if edit.operation == EditItem.OP_DELETE:
                edit.left.deleted = True
            elif edit.operation == EditItem.OP_MATCH:
                edit.left.matchNode = edit.right
                edit.right.matchNode = edit.left
            elif edit.operation == EditItem.OP_RENAME:
                edit.left.matchNode = edit.right
                edit.right.matchNode = edit.left
            else:
                newEdits.append(edit)

        self.matchNode.markInsertTrees()
        self.markDeleteTrees()

        while True:
            editList = newEdits
            newEdits = []

            for edit in editList:
                # Already processed
                if edit.right.matchNode is not None:
                    continue

                if edit.right.insertTree:
                    matchingParent = edit.right.parent.matchNode
                    if matchingParent is None:
                        # we don't know where it goes yet
                        newEdits.append(edit)
                        continue

                    # If a node has no children, then we can add it as a child
                    if edit.right.parent.matchNode.children is None or \
                       len(edit.right.parent.matchNode.children) == 0:
                        if edit.right.parent.matchNode.children is None:
                            edit.right.parent.matchNode.children = []
                        edit.right.parent.matchNode.children.append(
                            edit.right.cloneTree(edit.right.parent.matchNode))
                        continue

                    # If we have a matched preceeding node, put it after that one
                    sibling = edit.right.parent.getPredecessor(edit.right)
                    if sibling is not None:
                        if sibling.matchNode is not None:
                            newNode2 = edit.right.cloneTree(matchingParent)
                            matchingParent.insertAfter(sibling.matchNode, newNode2)
                            continue

                    # If we have a matching successor node, put it after that one
                    sibling = edit.right.parent.getSuccessor(edit.right)
                    if sibling is not None:
                        if sibling.matchNode is not None:
                            newNode2 = edit.right.cloneTree(matchingParent)
                            matchingParent.insertBefore(sibling.matchNode, newNode2)
                            continue

                    # If all of the left children are deleted and a new right is added.
                    allDeleted = True
                    for child in matchingParent.children:
                        if not child.deleteTree:
                            allDeleted = False
                            break

                    if allDeleted:
                        newNode2 = edit.right.cloneTree(matchingParent)
                        matchingParent.children.append(newNode2)
                        continue

                    newEdits.append(edit)
                    continue

                # Nodes which have undealt with children are deferred
                f = True
                for child in edit.right.children:
                    if child.matchNode is None and not child.insertTree:
                        f = False
                        break
                if not f:
                    newEdits.append(edit)
                    continue

                # Get the list of children that we need to match
                matchList = []
                for child in edit.right.children:
                    if not child.inserted and not child.insertTree:
                        matchList.append(child.matchNode)
                if len(matchList) == 0:
                    newEdits.append(edit)
                    continue

                # Build the list of all common ancestors of these nodes
                commonParents = None
                for child in matchList:
                    c = child.parent
                    ancestorList = []
                    while c is not None:
                        ancestorList.append(c)
                        c = c.parent
                    ancestorList = ancestorList[::-1]
                    if commonParents is None:
                        commonParents = ancestorList
                    else:
                        for i in range(min(len(ancestorList), len(commonParents))):
                            if ancestorList[i] != commonParents[i]:
                                commonParents = commonParents[:i]
                                break
                matchParent = commonParents[-1]

                # create the new node
                newNode = edit.right.clone()
                newNode.parent = matchParent
                newNode.inserted = True
                newNode.matchNode = edit.right
                edit.right.matchNode = newNode

                #

                i = 0
                iX = -1
                interums = []
                for child in edit.right.children:
                    if child.insertTree:
                        newNode2 = child.cloneTree(None)
                        newNode.children.append(newNode2)
                        continue
                    while i != len(matchParent.children):
                        if matchParent.children[i].isMatchNode(child.matchNode):
                            if len(interums) != 0:
                                if iX != -1:
                                    for ii in interums:
                                        newNode.children.append(matchParent.children[ii])
                                        matchParent.children[ii] = newNode
                                        del matchParent.children[ii]
                                        i -= 1
                                interums = []
                            newNode.children.append(matchParent.children[i])
                            matchParent.children[i].parent = newNode
                            del matchParent.children[i]
                            if iX == -1:
                                iX = i
                            break
                        else:
                            interums.append(i)
                        i += 1

                if iX == -1:
                    iX = 0
                matchParent.children.insert(iX, newNode)

            if len(editList) == len(newEdits):
                break

        log.note("Number of edits left = " + str(len(newEdits)))
        for edit in newEdits:
            log.note(edit.toString())
        return len(newEdits)


class DiffPI(DiffRoot):
    def __init__(self, xmlNode, parent):
        DiffRoot.__init__(self, xmlNode, parent)

    def ToHtml(self, parent):
        root2 = E.LI()
        parent.append(root2)
        root = E.SPAN()
        root2.append(root)
        if self.inserted:
            root.attrib['class'] = 'right'
            root.attrib["whereRight"] = "R{0}_{1}".format(self.xml.sourceline, 0)
        elif self.deleted:
            root.attrib['class'] = 'left'
            root.attrib["whereLeft"] = "L{0}_{1}".format(self.xml.sourceline, 0)
        elif self.matchNode is None:
            root.attrib['class'] = 'error'
        else:
            root.attrib["whereLeft"] = "L{0}_{1}".format(self.xml.sourceline, 0)
            root.attrib["whereRight"] = "R{0}_{1}".format(self.matchNode.xml.sourceline, 0)
            if self.xml.target == self.matchNode.xml.target:
                if self.xml.text == self.matchNode.xml.text:
                    pass
                else:
                    root.text = "<?{0} ".format(self.xml.target)
                    s = E.SPAN()
                    s.attrib['class'] = 'left'
                    s.text = self.xml.text
                    root.append(s)
                    s = E.SPAN()
                    s.attrib['class'] = 'right'
                    s.text = self.matchNode.xml.text
                    root.append(s)
                    s.tail = "?>"
                    return
            else:
                root.text = "<?"
                s = E.SPAN()
                s.attrib['class'] = 'left'
                s.text = self.xml.target
                root.append(s)
                s = E.SPAN()
                s.attrib['class'] = 'right'
                s.text = self.matchNode.xml.target
                root.append(s)
                s.tail = ' '
                s = E.SPAN()
                s.attrib['class'] = 'left'
                s.text = self.xml.text
                root.append(s)
                s = E.SPAN()
                s.attrib['class'] = 'right'
                s.text = self.matchNode.xml.text
                root.append(s)
                s.tail = "?>"
                return

        root.text = "<?{0} {1}?>".format(self.xml.target, self.xml.text)

    def cloneTree(self, parent):
        clone = DiffPI(self.xml, parent)
        clone.matchNode = self
        clone.inserted = True
        self.matchNode = clone
        return clone

    def updateCost(self, right):
        if self.xml.target == right.xml.target:
            if self.xml.text == right.xml.text:
                return 0
            else:
                return 50
        return 100


class DiffComment(DiffRoot):
    def __init__(self, xmlNode, parent):
        DiffRoot.__init__(self, xmlNode, parent)
        self.preserve = True

    def ToHtml(self, parent):
        node = E.LI()
        parent.append(node)
        if self.inserted:
            n = E.SPAN()
            n.attrib['class'] = 'artwork right'
            node.attrib["whereRight"] = "R{0}_{1}".format(self.xml.sourceline, 0)
            self.fixPreserveSpace(n, "<-- {0} -->".format(self.toText()))
            node.append(n)
        elif self.deleted:
            n = E.SPAN()
            n.attrib['class'] = 'artwork left'
            node.attrib["whereLeft"] = "L{0}_{1}".format(self.xml.sourceline, 0)
            self.fixPreserveSpace(n, "<-- {0} -->".format(self.toText()))
            node.append(n)
        elif self.matchNode is None:
            n = E.SPAN()
            root.attrib['class'] = 'artwork error'
            self.fixPreserveSpace(n, "<-- {0} -->".format(self.toText()))
            node.append(n)
        else:
            node.attrib["whereLeft"] = "L{0}_{1}".format(self.xml.sourceline, 0)
            node.attrib["whereRight"] = "R{0}_{1}".format(self.matchNode.xml.sourceline, 0)
            left = "<-- {0} -->".format(self.toText())
            right = "<-- {0} -->".format(self.matchNode.toText(), node)
            self.diffTextToHtml(left, right, node)

    def toText(self):
        return self.xml.text

    def cloneTree(self, parent):
        clone = DiffComment(self.xml, parent)
        clone.matchNode = self
        clone.inserted = True
        self.matchNode = clone
        return clone

    def updateCost(self, right):
        if self.xml.text == right.xml.text:
            return 0
        return 3


class DiffElement(DiffRoot):
    def __init__(self, xmlNode, parent):
        if not isinstance(xmlNode, DiffElement):
            DiffRoot.__init__(self, xmlNode, parent)

            if xmlNode.text is not None:
                self.children.append(DiffText(xmlNode.text, xmlNode, self))

            for c in xmlNode.iterchildren():
                self.children.append(self.createNode(c, self))
                if c.tail is not None and c.tail.rstrip() != '':
                    self.children.append(DiffText(c.tail, xmlNode, self))
        else:
            DiffRoot.__init__(self, xmlNode.xml, parent)

    def cloneTree(self, root):
        clone = DiffElement(self, root)
        clone.matchNode = self
        clone.inserted = True
        self.matchNode = clone

        for child in self.children:
            clone.children.append(child.cloneTree(clone))
        return clone

    def clone(self):
        clone = DiffElement(self, None)
        return clone

    def ToHtml(self, parent):
        # If we have the right doc info - then emit the <?xml?> line

        root = E.LI()
        parent.append(root)
        anchor = root
        if self.deleted:
            # anchor.attrib['onclick'] = 'return sync2here(1, {0}, -1, 0)'.
            # format(self.xml.sourceline)
            node = E.SPAN()
            node.attrib["class"] = 'left'
            root.attrib["whereLeft"] = "L{0}_{1}".format(self.xml.sourceline, 0)
            node.text = "<" + self.xml.tag
            anchor.append(node)
            if len(self.xml.attrib):
                for key in self.xml.attrib.iterkeys():
                    node.text = node.text + " " + key + '="' + self.xml.attrib[key] + '"'
        elif self.inserted:
            # anchor.attrib['onclick'] = 'return sync2here(-1, 0, 1, {0})'.
            # format(self.xml.sourceline)
            node = E.SPAN()
            node.attrib['class'] = 'right'
            root.attrib["whereRight"] = "R{0}_{1}".format(self.xml.sourceline, 0)
            node.text = "<" + self.xml.tag
            anchor.append(node)
            if len(self.xml.attrib):
                for key in self.xml.attrib.iterkeys():
                    node.text = node.text + " " + key + '="' + self.xml.attrib[key] + '"'
        elif self.matchNode is None:
            # anchor.attrib['onclick'] = 'return sync2here(1, {0}, -1, 1)'.
            # format(self.xml.sourceline)
            node = E.SPAN()
            node.attrib['class'] = 'error'
            node.text = "<" + self.xml.tag
            anchor.append(node)
            if len(self.xml.attrib):
                for key in self.xml.attrib.iterkeys():
                    node.text = node.text + " " + key + '="' + self.xml.attrib[key] + '"'
        else:
            root.attrib["whereLeft"] = "L{0}_{1}".format(self.xml.sourceline, 0)
            root.attrib["whereRight"] = "R{0}_{1}".format(self.matchNode.xml.sourceline, 0)
            # anchor.attrib['onclick'] = 'return sync2here(1, {0},  1, {1})' \
            #      .format(self.xml.sourceline, self.matchNode.xml.sourceline)
            if self.xml.tag == self.matchNode.xml.tag:
                anchor.text = "<" + self.xml.tag
            else:
                anchor.text = "<"
                node = E.SPAN()
                node.attrib['class'] = 'left'
                node.text = self.xml.tag
                anchor.append(node)
                node = E.SPAN()
                node.attrib['class'] = 'right'
                node.text = self.matchNode.xml.tag
                anchor.append(node)
            if len(self.xml.attrib):
                for key in self.xml.attrib.iterkeys():
                    if key in self.matchNode.xml.attrib and \
                       self.xml.attrib[key] == self.matchNode.xml.attrib[key]:
                        node = E.SPAN()
                        node.text = " " + key + '="' + self.xml.attrib[key] + '"'
                        anchor.append(node)
                    else:
                        node = E.SPAN()
                        node.attrib['class'] = 'left'
                        node.text = " " + key + '="' + self.xml.attrib[key] + '"'
                        anchor.append(node)
                        if key in self.matchNode.xml.attrib:
                            node = E.SPAN()
                            node.attrib['class'] = 'right'
                            node.text = " " + key + '="' + self.matchNode.xml.attrib[key] + '"'
                            anchor.append(node)

            for key in self.matchNode.xml.attrib.iterkeys():
                if key not in self.xml.attrib:
                    node = E.SPAN()
                    node.attrib['class'] = 'right'
                    node.text = " " + key + '="' + self.matchNode.xml.attrib[key] + '"'
                    anchor.append(node)

        if len(self.children):
            s = E.SPAN()
            s.text = ">"
            if self.deleted:
                s.attrib['class'] = 'left'
            elif self.inserted:
                s.attrib['class'] = 'right'
            anchor.append(s)
            ul = E.UL()
            for child in self.children:
                child.ToHtml(ul)

            li = E.LI()
            s = E.SPAN()
            li.append(s)
            s.text = "</" + self.xml.tag + ">"
            if self.deleted:
                s.attrib['class'] = 'left'
                li.attrib["whereLeft"] = "L{0}_{1}".format(self.xml.sourceline, 0)
            elif self.inserted:
                s.attrib['class'] = 'right'
                li.attrib["whereRight"] = "R{0}_{1}".format(self.xml.sourceline, 0)
            else:
                li.attrib["whereLeft"] = "L{0}_{1}".format(self.xml.sourceline, 0)
                li.attrib["whereRight"] = "R{0}_{1}".format(self.matchNode.xml.sourceline, 0)
                # li.attrib["src"] = "DiffElement-End"

            ul.append(li)
            root.append(ul)
        else:
            s = E.SPAN()
            s.text = "/>"
            if self.deleted:
                s.attrib['class'] = 'left'
            elif self.inserted:
                s.attrib['class'] = 'right'
            anchor.append(s)

    def updateCost(self, right):
        if self.xml.tag == right.xml.tag:
            return 0
        if tagMatching is not None:
            if self.xml.tag in tagMatching and right.xml.tag in tagMatching[self.xml.tag]:
                return 0
        return 100

    def decorateSource(self, sourceLines):
        source = sourceLines[self.xml.sourceLine]
        if self.deleted:
            pass
        elif self.inserted:
            pass
        elif self.matchNode is None:
            pass
        else:
            if self.xml.tag != self.matchNode.xml.tag:
                source.replace("&amp;"+self.xml.tag, "<span class='left'>&amp;" + self.xml.tag)

        sourceLines[self.xml.sourceLine] = source


class DiffText(DiffRoot):
    def __init__(self, text, xmlNode, parent):
        DiffRoot.__init__(self, xmlNode, parent)
        self.text = text

    def cloneTree(self, parent):
        clone = DiffText(self.text, self.xml, parent)
        clone.matchNode = self
        clone.inserted = True
        self.matchNode = clone
        return clone

    def toText(self):
        return self.text

    def ToHtml(self, parent):
        node = E.LI()
        parent.append(node)
        if self.deleted:
            n = E.SPAN()
            n.attrib["class"] = 'left'
            node.attrib["whereLeft"] = "L{0}_{1}".format(self.xml.sourceline, 0)
            n.text = self.text
            node.append(n)
        elif self.inserted:
            n = E.SPAN()
            n.attrib["class"] = 'right'
            node.attrib["whereRight"] = "R{0}_{1}".format(self.xml.sourceline, 0)
            n.text = self.text
            node.append(n)
        elif self.matchNode is None:
            n = E.SPAN()
            n.attrib["class"] = 'error'
            n.text = self.text
            node.append(n)
        else:
            node.attrib["whereLeft"] = "L{0}_{1}".format(self.xml.sourceline, 0)
            node.attrib["whereRight"] = "R{0}_{1}".format(self.matchNode.xml.sourceline, 0)
            if self.text == self.matchNode.text:
                node.text = self.text
            else:
                n = E.SPAN()
                n.attrib['class'] = 'left'
                n.text = self.text
                node.append(n)
                n = E.SPAN()
                n.attrib['class'] = 'right'
                n.text = self.matchNode.text
                node.append(n)

    def updateCost(self, right):
        if self.text == right.text:
            return 0
        return 3

    def decorateSource(self, sourceLines):
        pass


class DiffParagraph(DiffRoot):
    def __init__(self, node, parent):
        if not isinstance(node, DiffParagraph):
            DiffRoot.__init__(self, node, parent)
        else:
            DiffRoot.__init__(self, node.xml, parent)
        self.preserve = False
        if '{http://www.w3.org/XML/1998/namespace}space' in self.xml.attrib:
            if self.xml.attrib['{http://www.w3.org/XML/1998/namespace}space'] == 'preserve':
                self.preserve = True
        elif self.xml.tag in PreserveSpace:
            self.preserve = True

    def cloneTree(self, root):
        clone = DiffParagraph(self, root)
        clone.matchNode = self
        clone.inserted = True
        self.matchNode = clone

        for child in self.children:
            clone.children.append(child.cloneTree(clone))
        return clone

    def decorateSource(self):
        for child in self.children:
            child.decorateSource(sourceLines)

    def toText(self):
        text = ""
        for child in self.children:
            x = child.toText()
            if type(x).__name__ == 'bytes':
                x = x.decode('utf-8')
            text += x

        return text

    def ToHtml(self, parent):

        node = E.LI()
        parent.append(node)
        if self.deleted:
            n = E.SPAN()
            n.attrib["class"] = 'left'
            node.attrib["whereLeft"] = "L{0}_{1}".format(self.xml.sourceline, 0)
            self.fixPreserveSpace(n, self.toText())
            node.append(n)
        elif self.inserted:
            n = E.SPAN()
            n.attrib['class'] = 'right'
            node.attrib["whereRight"] = "R{0}_{1}".format(self.xml.sourceline, 0)
            self.fixPreserveSpace(n, self.toText())
            node.append(n)
        elif self.matchNode is None:
            n = E.SPAN()
            n.attrib['class'] = 'error'
            self.fixPreserveSpace(n, self.toText())
            node.append(n)
        else:
            self.diffTextToHtml(self.toText(), self.matchNode.toText(), node)
            node.attrib["whereLeft"] = "L{0}_{1}".format(self.xml.sourceline, 0)
            node.attrib["whereRight"] = "R{0}_{1}".format(self.matchNode.xml.sourceline, 0)

    def updateCost(self, right):
        leftText = self.toText()
        rightText = right.toText()
        differ = difflib.SequenceMatcher(a=leftText, b=rightText)
        ratio = differ.quick_ratio()
        return 10 - int(math.floor(ratio*10))
