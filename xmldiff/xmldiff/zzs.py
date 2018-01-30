#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

def py_zeros(dim, pytype):
    assert len(dim) == 2
    return [[pytype() for y in range(dim[1])]
            for x in range(dim[0])]

try:
    from editdist import distance as strdist
except ImportError:
    def strdist(a, b):
        if a == b:
            return 0
        else:
            return 1


class EditItem(object):
    OP_INSERT = 1
    OP_DELETE = 2
    OP_RENAME = 3
    OP_MATCH = 4
    OP_COMBINE = 5

    def __init__(self, operation, left, right):
        self.operation = operation
        self.left = left
        self.right = right
        self.cost = 0
        if left is not None and isinstance(left, EditItem):
            self.cost += left.cost
        if right is not None and isinstance(right, EditItem):
            self.cost += right.cost

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

    def treedist(i, j):
        Al = A.lmds
        Bl = B.lmds
        An = A.nodes
        Bn = B.nodes

        m = i - Al[i] + 2
        n = j - Bl[j] + 2
        fd = py_zeros((m, n), int)

        ioff = Al[i] - 1
        joff = Bl[j] - 1

        for x in range(1, m):  # δ(l(i1)..i, θ) = δ(l(1i)..1-1, θ) + γ(v → λ)
            fd[x][0] = EditItem(EditItem.OP_COMBINE, fd[x-1][0], remove_cost(An[x+ioff]))
        for y in range(1, n):  # δ(θ, l(j1)..j) = δ(θ, l(j1)..j-1) + γ(λ → w)
            fd[0][y] = EditItem(EditItem.OP_COMBINE, fd[0][y-1], insert_cost(Bn[y+joff]))

        for x in range(1, m):  # the plus one is for the xrange impl
            for y in range(1, n):
                # only need to check if x is an ancestor of i
                # and y is an ancestor of j
                if Al[i] == Al[x+ioff] and Bl[j] == Bl[y+joff]:
                    #                   +-
                    #                   | δ(l(i1)..i-1, l(j1)..j) + γ(v → λ)
                    # δ(F1 , F2 ) = min-+ δ(l(i1)..i , l(j1)..j-1) + γ(λ → w)
                    #                   | δ(l(i1)..i-1, l(j1)..j-1) + γ(v → w)
                    #                   +-
                    op1 = EditItem(EditItem.OP_COMBINE, fd[x-1][y], remove_cost(An[x+ioff]))
                    op2 = EditItem(EditItem.OP_COMBINE, fd[x][y-1], insert_cost(Bn[y+joff]))
                    op3 = EditItem(EditItem.OP_COMBINE, fd[x-1][y-1],
                                   update_cost(An[x+ioff], Bn[y+joff]))
                    if op1.cost < op2.cost:
                        if op1.cost < op3.cost:
                            fd[x][y] = op1
                        elif op2.cost < op3.cost:
                            fd[x][y] = op2
                        else:
                            fd[x][y] = op3
                    else:
                        if op2.cost < op3.cost:
                            fd[x][y] = op2
                        else:
                            fd[x][y] = op3

                    # fd[x][y] = min(
                    #     fd[x-1][y] + remove_cost(An[x+ioff]),
                    #     fd[x][y-1] + insert_cost(Bn[y+joff]),
                    #     fd[x-1][y-1] + update_cost(An[x+ioff], Bn[y+joff]),
                    # )
                    treedists[x+ioff][y+joff] = fd[x][y]
                else:
                    #                   +-
                    #                   | δ(l(i1)..i-1, l(j1)..j) + γ(v → λ)
                    # δ(F1 , F2 ) = min-+ δ(l(i1)..i , l(j1)..j-1) + γ(λ → w)
                    #                   | δ(l(i1)..l(i)-1, l(j1)..l(j)-1)
                    #                   |                     + treedist(i1,j1)
                    #                   +-
                    p = Al[x+ioff]-1-ioff
                    q = Bl[y+joff]-1-joff
                    # print (p, q), (len(fd), len(fd[0]))
                    op1 = EditItem(EditItem.OP_COMBINE, fd[x-1][y], remove_cost(An[x+ioff]))
                    op2 = EditItem(EditItem.OP_COMBINE, fd[x][y-1], insert_cost(Bn[y+joff]))
                    op3 = EditItem(EditItem.OP_COMBINE, fd[p][q], treedists[x+ioff][y+joff])

                    if op1.cost < op2.cost:
                        if op1.cost < op3.cost:
                            fd[x][y] = op1
                        elif op2.cost < op3.cost:
                            fd[x][y] = op2
                        else:
                            fd[x][y] = op3
                    else:
                        if op2.cost < op3.cost:
                            fd[x][y] = op2
                        else:
                            fd[x][y] = op3

                    # fd[x][y] = min(
                    #     fd[x-1][y] + remove_cost(An[x+ioff]),
                    #     fd[x][y-1] + insert_cost(Bn[y+joff]),
                    #     fd[p][q] + treedists[x+ioff][y+joff]
                    # )

    for i in A.keyroots:
        for j in B.keyroots:
            treedist(i, j)

    return treedists[-1][-1]