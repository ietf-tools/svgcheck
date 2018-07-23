import re
import sys
import os

Console = sys.stdout

def ComputeEdits(leftArray, rightArray):
    leftIndex = [ i for i in range(len(leftArray)) if not allspaces(leftArray[i]) ]
    rightIndex = [ i for i in range(len(rightArray)) if not allspaces(rightArray[i]) ]

    d = {}
    S = len(leftIndex)
    T = len(rightIndex)

    d[0, 0] = 0
    for i in range(1, S):
        d[i, 0] = d[i-1, 0] + (4 if '\n' in leftArray[leftIndex[i]] else 1)

    for j in range(1, T):
        d[0, j] = d[0, j-1] + (4 if '\n' in rightArray[rightIndex[j]] else 1)

    for j in range(1, T):
        for i in range(1, S):
            left = leftArray[leftIndex[i]]
            right = rightArray[rightIndex[j]]
            if left == right:
                d[i, j] = d[i-1, j-1]
            elif '\n' in left and '\n' in right:
                d[i, j] = d[i-1, j-1]
            else:
                d[i, j] = min(d[i-1, j] + (d[i, 0] - d[i-1, 0]),   # Insert
                              d[i, j-1] + (d[0, j] - d[0, j-1]),   # Delete
                              d[i-1, j-1] + d[i,0] - d[i-1, 0] + d[0, j] - d[0, j-1])  # Change = max(Insert + Delete)

    i = S - 1
    j = T - 1
    val = d[i, j]
    ops = []
    leftIndex.append(i+1)
    rightIndex.append(j+1)

    op = ['nop', i, i, j, j]

    while (i >= 0 and j >= 0):
        if i == 0:
            if j == 0:
                op1 = ['equal', leftIndex[i], leftIndex[i+1], rightIndex[j], rightIndex[j+1]]
                j -= 1
                i -= 1
            else:
                op1 = ['insert', leftIndex[i], leftIndex[i], rightIndex[j], rightIndex[j+1]]
                j -= 1
        elif j == 0:
            op1 = ['remove', leftIndex[i], leftIndex[i+1], rightIndex[j], rightIndex[j]]
            i -= 1
        else:
            if d[i, j] == d[i-1, j-1] and d[i-1, j-1] < d[i-1, j] and d[i-1, j-1] < d[i, j-1]:
                op1 = ['equal', leftIndex[i], leftIndex[i+1], rightIndex[j], rightIndex[j+1]]
                i -= 1
                j -= 1
            elif d[i-1, j] <= d[i, j-1]:
                op1 = ['remove', leftIndex[i], leftIndex[i+1], rightIndex[j], rightIndex[j]]
                i -= 1
            else:
                op1 = ['insert', leftIndex[i], leftIndex[i], rightIndex[j], rightIndex[j+1]]
                j -= 1
        
        if op1[0] == op[0]:
            op[1] = op1[1]
            op[3] = op1[3]
        else:
            ops.append(op)
            op = op1
    
    ops.append(op)
    ops = ops[1:]
    ops = list(ops)
    ops.reverse()

    return ops


def allspaces(text):
    return False
    if len(text) == 0:
        return True
    if not text.isspace():
        return False
    if '\n' in text:
        return False
    return True

def LD(s,t):
    s = ' ' + s
    t = ' ' + t
    d = {}
    S = len(s)
    T = len(t)
    for i in range(S):
        d[i, 0] = i
    for j in range (T):
        d[0, j] = j
    for j in range(1,T):
        for i in range(1,S):
            if s[i] == t[j]:
                d[i, j] = d[i-1, j-1]
            else:
                d[i, j] = min(d[i-1, j], d[i, j-1], d[i-1, j-1]) + 1
    return d[S-1, T-1]

def doWhiteArray(text):
    result = []
    #  At some point I want to split whitespace with
    #  CR in them to multiple lines
    for right in re.split(r'([\s\xa0]+)', text):
        if right.isspace():
            result.extend(list(right))
        else:
            result.append(right)
    return result


if __name__ == '__main__':
    old = "This is\xa0a\xa0message\nwith one change"
    new = "This is\xa0a message with\ntwo change"
    leftArray = doWhiteArray(old)
    rightArray = doWhiteArray(new)

    ops = ComputeEdits(leftArray, rightArray)

    for op in ops:
        Console.write("%s %2d %2d %2d %2d '%s' '%s'\n" % (op[0], op[1], op[2], op[3], op[4], ''.join(leftArray[op[1]:op[2]]), ''.join(rightArray[op[3]:op[4]])))

    Console.write("**********************************************\n")

    old = "In <xref target=\"RFC8032\"/> the elliptic curve signature system Edwards-curve Digital Signature Algorithm (EdDSA) is described along with a recommendation for the use of the curve25519 and curve448. EdDSA has defined two modes, the PureEdDSA mode without pre-hashing, and the HashEdDSA mode with pre-hashing.\n<!--\xa0Remove\xa0pre-hash\nThe\xa0Ed25519ph\xa0and\xa0Ed448ph\xa0algorithm\xa0definitions\xa0specify\xa0the\xa0one-way\xa0hash\xa0function\xa0that\xa0is\xa0used\xa0for\xa0pre-hashing.\nThe\xa0convention\xa0used\xa0for\xa0identifying\xa0the\xa0algorithm/curve\xa0combinations\xa0are\xa0to\xa0use\xa0the\xa0Ed25519\xa0and\xa0Ed448\xa0for\xa0the\xa0PureEdDSA\xa0mode,\xa0with\xa0Ed25519ph\xa0and\xa0Ed448ph\xa0for\xa0the\xa0HashEdDSA\xa0mode.\n-->\nThe convention used for identifying the algorithm/curve combinations is to use \"Ed25519\" and \"Ed448\" for the PureEdDSA mode. The document does not provide the conventions needed for the pre-hash versions of the signature algorithm. The use of the OIDs is described for public keys, private keys and signatures."
    new = "In <xref target=\"RFC8032\"/> the elliptic curve signature system Edwards-curve Digital Signature Algorithm (EdDSA) is described along with a recommendation for the use of the curve25519 and curve448.  EdDSA has defined two modes: the PureEdDSA mode without prehashing and the HashEdDSA mode with prehashing.  The convention used for identifying the algorithm/curve combinations is to use \"Ed25519\" and \"Ed448\" for the PureEdDSA mode.  This document does not provide the conventions needed for the prehash versions of the signature algorithm.  The use of the OIDs is described for public keys, private keys and signatures."

    leftArray = doWhiteArray(old)
    rightArray = doWhiteArray(new)
    ops = ComputeEdits(leftArray, rightArray)
    for op in ops:
        Console.write("%s %2d %2d %2d %2d '%s' '%s'\n" % (op[0], op[1], op[2], op[3], op[4], ''.join(leftArray[op[1]:op[2]]), ''.join(rightArray[op[3]:op[4]])))
