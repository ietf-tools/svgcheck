from xmldiff._zzs import ffi, lib
from xmldiff.DiffNode import DiffElement, DiffParagraph, DiffComment
from xmldiff.EditItem import EditItem

all_handles = []
last_child = None


@ffi.def_extern()
def zzs_get_children(node):
    global last_child
    treeNode = ffi.from_handle(node)
    childs = []
    if not isinstance(treeNode, DiffParagraph):
        for child in treeNode.children:
            h = ffi.new_handle(child)
            childs.append(h)
            all_handles.append(h)

    p = ffi.new("struct cArray *", [len(childs), childs])
    last_child = p
    return p


@ffi.def_extern()
def zzs_insert_cost(node):
    treeNode = ffi.from_handle(node)
    return 1


@ffi.def_extern()
def zzs_remove_cost(node):
    treeNode = ffi.from_handle(node)
    return treeNode.deleteCost()


@ffi.def_extern()
def zzs_update_cost(node1, node2):
    leftNode = ffi.from_handle(node1)
    rightNode = ffi.from_handle(node2)
    if type(leftNode) is not type(rightNode):
        return 100000
    cost = leftNode.updateCost(rightNode)
    return cost


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
