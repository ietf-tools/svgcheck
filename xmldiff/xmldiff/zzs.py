#!/Usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------
# Copyright The IETF Trust 2018-9, All Rights Reserved
# ----------------------------------------------------
#  Adapted from code by
# Authors: Tim Henderson and Steve Johnson
# Email: tim.tadh@gmail.com, steve@steveasleep.com
# For licensing see the LICENSE file in the top level directory.
#
#  The original code just computed the difference and did not bother with the set of
#  edits that were needed.  We care about the edits themselves.

from __future__ import absolute_import
from six.moves import range

import collections

"""
def py_zeros(dim, pytype):
    assert len(dim) == 2
    return [[pytype for y in range(dim[1])]
            for x in range(dim[0])]
"""

try:
    from editdist import distance as strdist
except ImportError:
    def strdist(a, b):
        if a == b:
            return 0
        else:
            return 1


class EditItem(object):
    __slots__ = ['operation', 'left', 'right', 'cost']
    OP_INSERT = 1
    OP_DELETE = 2
    OP_RENAME = 3
    OP_MATCH = 4
    OP_COMBINE = 5

    def __init__(self):
        self.cost = 0
        self.operation = 0
        self.left = None
        self.right = None
        pass

    def reset(self):
        self.operation = 0
        self.cost = 0
        self.left = None
        self.right = None

    def setOperation(self, operation, left, right):
        self.operation = operation
        self.left = left
        self.right = right
        self.cost = 0
        if left is not None and isinstance(left, EditItem):
            self.cost += left.cost
        if right is not None and isinstance(right, EditItem):
            self.cost += right.cost

    def clone(self):
        cloneOut = EditItem()
        returnValue = cloneOut
        cloneOut.operation = self.operation
        cloneOut.cost = self.cost
        stack = []
        if self.left is not None:
            stack.append((1, cloneOut, self))
        if self.right is not None:
            stack.append((0, cloneOut, self))

        while len(stack) > 0:
            side, node, node1 = stack.pop()
            xx = node1.left if side else node1.right

            if xx is not None:
                if isinstance(xx, EditItem):
                    if xx.operation == 0:
                        continue
                    if xx.operation == EditItem.OP_COMBINE:
                        newNode = EditItem()
                        newNode.operation = xx.operation
                        newNode.cost = xx.cost
                        if xx.left is not None:
                            stack.append((1, newNode, xx))
                        if xx.right is not None:
                            stack.append((0, newNode, xx))
                    else:
                        newNode = xx
                else:
                    newNode = xx
                if side:
                    node.left = newNode
                else:
                    node.right = newNode

        return returnValue

    def toList(self):
        list = []
        self._toList(list)
        return list

    def _toList(self, list):
        if self.operation != EditItem.OP_COMBINE:
            list.append(self)
            return
        if self.left is not None and isinstance(self.left, EditItem):
            self.left._toList(list)
        if self.right is not None and isinstance(self.right, EditItem):
            self.right._toList(list)

    def toString(self):
        left = ""
        right = ""
        if self.left:
            left = "left= {:>3}".format(self.left.index)
        if self.right:
            right = " right= {:>3}".format(self.right.index)
        txt = "OP={0} {1:>9}{2}".format(str(self.operation), left, right)
        return txt


class AnnotatedTree(object):

    def __init__(self, root, get_children):
        self.get_children = get_children

        self.root = root
        self.nodes = list()  # a post-order enumeration of the nodes in the tree
        self.ids = list()    # a matching list of ids
        self.lmds = list()   # left most descendents
        self.keyroots = None

        # k and k' are nodes specified in the post-order enumeration.
        # keyroots = {k | there exists no k'>k such that lmd(k) == lmd(k')}
        # see paper for more on keyroots

        stack = list()
        pstack = list()
        stack.append((root, collections.deque()))
        j = 0
        while len(stack) > 0:
            n, anc = stack.pop()
            nid = j
            for c in self.get_children(n):
                a = collections.deque(anc)
                a.appendleft(nid)
                stack.append((c, a))
            pstack.append(((n, nid), anc))
            j += 1
        lmds = dict()
        keyroots = dict()
        i = 0
        while len(pstack) > 0:
            (n, nid), anc = pstack.pop()
            # print list(anc)
            self.nodes.append(n)
            self.ids.append(nid)
            # print n.label, [a.label for a in anc]
            if not self.get_children(n):
                lmd = i
                for a in anc:
                    if a not in lmds:
                        lmds[a] = i
                    else:
                        break
            else:
                try:
                    lmd = lmds[nid]
                except Exception:
                    import pdb
                    pdb.set_trace()
            self.lmds.append(lmd)
            keyroots[lmd] = i
            i += 1
        self.keyroots = sorted(keyroots.values())


def distance(A, B, get_children, insert_cost, remove_cost, update_cost):
    '''Computes the exact tree edit distance between trees A and B with a
    richer API than :py:func:`zss.simple_distance`.
    Use this function if either of these things are true:
    * The cost to insert a node is **not** equivalent to the cost of changing
      an empty node to have the new node's label
    * The cost to remove a node is **not** equivalent to the cost of changing
      it to a node with an empty label
    Otherwise, use :py:func:`zss.simple_distance`.
    :param A: The root of a tree.
    :param B: The root of a tree.
    :param get_children:
        A function ``get_children(node) == [node children]``.  Defaults to
        :py:func:`zss.Node.get_children`.
    :param insert_cost:
        A function ``insert_cost(node) == cost to insert node >= 0``.
    :param remove_cost:
        A function ``remove_cost(node) == cost to remove node >= 0``.
    :param update_cost:
        A function ``update_cost(a, b) == cost to change a into b >= 0``.
    :return: An integer distance [0, inf+)
    '''
    A, B = AnnotatedTree(A, get_children), AnnotatedTree(B, get_children)
    # treedists = zeros((len(A.nodes), len(B.nodes)), int)
    treedists = [[None for x in range(len(B.nodes))] for y in range(len(A.nodes))]
    fd = [[EditItem() for x in range(len(B.nodes)+2)] for y in range(len(A.nodes)+2)]

    A_remove = [remove_cost(A.nodes[i]) for i in range(len(A.nodes))]
    B_insert = [insert_cost(B.nodes[i]) for i in range(len(B.nodes))]

    def treedist(i, j):
        Al = A.lmds
        Bl = B.lmds
        An = A.nodes
        Bn = B.nodes

        m = i - Al[i] + 2
        n = j - Bl[j] + 2

        for x in range(1, m):
            fd1 = fd[x]
            for y in range(1, n):
                fd1[y].reset()

        ioff = Al[i] - 1
        joff = Bl[j] - 1

        for x in range(1, m):  # δ(l(i1)..i, θ) = δ(l(1i)..1-1, θ) + γ(v → λ)
            fd[x][0].setOperation(EditItem.OP_COMBINE, fd[x-1][0], A_remove[x+ioff])
        fd1 = fd[0]
        for y in range(1, n):  # δ(θ, l(j1)..j) = δ(θ, l(j1)..j-1) + γ(λ → w)
            fd1[y].setOperation(EditItem.OP_COMBINE, fd1[y-1], B_insert[y+joff])

        for x in range(1, m):  # the plus one is for the xrange impl
            fd1 = fd[x]
            fdm1 = fd[x-1]
            x_ioff = x + ioff
            t = Al[i] == Al[x_ioff]
            remove = A_remove[x_ioff]
            treedists_1 = treedists[x_ioff]
            left = An[x_ioff]
            p = Al[x_ioff]-1-ioff
            fd_p = fd[p]
            y_joff = joff
            for y in range(1, n):
                y_joff += 1
                # only need to check if x is an ancestor of i
                # and y is an ancestor of j
                if t and Bl[j] == Bl[y_joff]:
                    #                   +-
                    #                   | δ(l(i1)..i-1, l(j1)..j) + γ(v → λ)
                    # δ(F1 , F2 ) = min-+ δ(l(i1)..i , l(j1)..j-1) + γ(λ → w)
                    #                   | δ(l(i1)..i-1, l(j1)..j-1) + γ(v → w)
                    #                   +-

                    insert = B_insert[y_joff]
                    update = update_cost(left, Bn[y_joff])

                    op1Cost = fdm1[y].cost + remove.cost
                    op2Cost = fd1[y-1].cost + insert.cost
                    op3Cost = fdm1[y-1].cost + update.cost

                    if op1Cost < op2Cost:
                        if op1Cost < op3Cost:
                            fd1[y].setOperation(EditItem.OP_COMBINE, fdm1[y], remove)
                        elif op2Cost < op3Cost:
                            fd1[y].setOperation(EditItem.OP_COMBINE, fd1[y-1], insert)
                        else:
                            fd1[y].setOperation(EditItem.OP_COMBINE, fdm1[y-1], update)
                    else:
                        if op2Cost < op3Cost:
                            fd1[y].setOperation(EditItem.OP_COMBINE, fd1[y-1], insert)
                        else:
                            fd1[y].setOperation(EditItem.OP_COMBINE, fdm1[y-1], update)

                    # fd[x][y] = min(
                    #     fd[x-1][y] + remove_cost(An[x+ioff]),
                    #     fd[x][y-1] + insert_cost(Bn[y+joff]),
                    #     fd[x-1][y-1] + update_cost(An[x+ioff], Bn[y+joff]),
                    # )
                    treedists_1[y_joff] = fd1[y].clone()
                else:
                    #                   +-
                    #                   | δ(l(i1)..i-1, l(j1)..j) + γ(v → λ)
                    # δ(F1 , F2 ) = min-+ δ(l(i1)..i , l(j1)..j-1) + γ(λ → w)
                    #                   | δ(l(i1)..l(i)-1, l(j1)..l(j)-1)
                    #                   |                     + treedist(i1,j1)
                    #                   +-
                    q = Bl[y_joff]-1-joff

                    insert = B_insert[y_joff]

                    op1Cost = fdm1[y].cost + remove.cost
                    op2Cost = fd1[y-1].cost + insert.cost
                    op3Cost = fd_p[q].cost + treedists_1[y_joff].cost

                    if op1Cost < op2Cost:
                        if op1Cost < op3Cost:
                            fd1[y].setOperation(EditItem.OP_COMBINE, fdm1[y], remove)
                        elif op2Cost < op3Cost:
                            fd1[y].setOperation(EditItem.OP_COMBINE, fd1[y-1], insert)
                        else:
                            fd1[y].setOperation(EditItem.OP_COMBINE, fd_p[q], treedists_1[y_joff])
                    else:
                        if op2Cost < op3Cost:
                            fd1[y].setOperation(EditItem.OP_COMBINE, fd1[y-1], insert)
                        else:
                            fd1[y].setOperation(EditItem.OP_COMBINE, fd_p[q], treedists_1[y_joff])

                    # fd[x][y] = min(
                    #     fd[x-1][y] + remove_cost(An[x+ioff]),
                    #     fd[x][y-1] + insert_cost(Bn[y+joff]),
                    #     fd[p][q] + treedists[x+ioff][y+joff]
                    # )

    for i in A.keyroots:
        for j in B.keyroots:
            treedist(i, j)

    return treedists[-1][-1]
