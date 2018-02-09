from xmldiff._zzs import ffi, lib
from xmldiff.DiffNode import DiffElement

all_handles = []
@ffi.def_extern()
def zzs_get_children(node):
    treeNode = ffi.from_handle(node)
    childs = []
    for child in treeNode.children:
        h = ffi.new_handle(child)
        childs.append(h)
        all_handles.append(h)

    p = ffi.new("struct cArray *", [len(childs), childs])
    return p

@ffi.def_extern()
def zzs_insert_cost(node):
    treeNode = ffi.from_handle(node)
    return 1

@ffi.def_extern()
def zzs_remove_cost(node):
    treeNode = ffi.from_handle(node)
    if isinstance(treeNode, DiffElement):
        return 10
    return 1

@ffi.def_extern()
def zzs_update_cost(node1, node2):
    leftNode = ffi.from_handle(node1)
    rightNode = ffi.from_handle(node2)
    if type(leftNode) is not type(rightNode):
        return 100000
    return leftNode.updateCost(rightNode)

class EditItem(object):
    __slots__ = ['operation', 'left', 'right', 'cost']
    OP_INSERT = 1
    OP_DELETE = 2
    OP_RENAME = 3
    OP_MATCH = 4
    OP_COMBINE = 5

    def __init__(self, data):
        self.cost = 0
        self.operation = data.operation
        if data.left is not None and data.left != ffi.NULL:
            self.left = ffi.from_handle(data.left)
        else:
            self.left = None
        self.right = None
        if data.right is not None and data.right != ffi.NULL:
            self.right = ffi.from_handle(data.right)

    def toString(self):
        left = ""
        right = ""
        if self.left:
            left = "left= {:>3}".format(self.left.index)
        if self.right:
            right = " right= {:>3}".format(self.right.index)
        txt = "OP={0} {1:>9}{2}".format(str(self.operation), left, right)
        return txt


def distance(leftXml, rightXml, get_children, insertCost, deleteCost, updateCost):
    global all_handles
    
    ll = ffi.new_handle(leftXml)
    rr = ffi.new_handle(rightXml)
    rv = lib.Distance(ll, rr, lib.zzs_get_children, lib.zzs_insert_cost, lib.zzs_remove_cost,
                      lib.zzs_update_cost)

    editList = []
    for i in range(rv.c):
        editList.append(EditItem(rv.rgEdits[i]))

    all_handles = []

    return editList

