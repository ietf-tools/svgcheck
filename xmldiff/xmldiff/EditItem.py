from xmldiff._zzs import ffi

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


