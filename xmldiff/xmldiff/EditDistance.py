import re
import sys
import os

Console = sys.stdout

def ComputeEdits(leftArray, rightArray):

    d = {}
    S = len(leftArray)
    T = len(rightArray)

    # skip over matching at the front
    minLength = min(S, T)
    opStart = ['equal', 0, minLength, 0, minLength]
    rangeStart = 0
    for i in range(minLength):
        if leftArray[i] != rightArray[i]:
            opStart[2] = i
            opStart[4] = i
            rangeStart = i
            break

    if opStart[2] == minLength and minLength == S and minLength == T:
        return [opStart]

    rangeEnd = 0
    opEnd = ['equal', S, S, T, T]
    for i in range(1, minLength-rangeStart-1):
        if leftArray[-i] != rightArray[-i]:
            rangeEnd = i - 1
            opEnd[1] = S-i + 1
            opEnd[3] = T-i + 1
            break

    leftIndex = [ i for i in range(rangeStart-1, len(leftArray)-rangeEnd) ]
    rightIndex = [ i for i in range(rangeStart-1, len(rightArray)-rangeEnd) ]

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


    # for i in range(S):
    #    Console.write(str(i))
    #    Console.write(": ")
    #    for j in range(T):
    #        Console.write(str(d[i, j]))
    #        Console.write(" ")
    #    Console.write("\n")

    i = S - 1
    j = T - 1
    val = d[i, j]
    ops = []
    leftIndex.append(leftIndex[-1]+1)
    rightIndex.append(rightIndex[-1]+1)

    op = opEnd

    while (i >= 0 and j >= 0):
        if i == 0:
            if j == 0:
                op1 = ['equal', leftIndex[i], leftIndex[i+1], rightIndex[j], rightIndex[j+1]]
                j -= 1
                i -= 1
                op1 = ['nop', 0, 0, 0, 0]
            else:
                op1 = ['insert', leftIndex[i+1], leftIndex[i+1], rightIndex[j], rightIndex[j+1]]
                j -= 1
        elif j == 0:
            op1 = ['remove', leftIndex[i], leftIndex[i+1], rightIndex[j+1], rightIndex[j+1]]
            i -= 1
        else:
            if d[i, j] == d[i-1, j-1] and d[i-1, j-1] < d[i-1, j] and d[i-1, j-1] < d[i, j-1]:
                op1 = ['equal', leftIndex[i], leftIndex[i+1], rightIndex[j], rightIndex[j+1]]
                i -= 1
                j -= 1
            elif d[i-1, j] <= d[i, j-1]:
                op1 = ['remove', leftIndex[i], leftIndex[i+1], rightIndex[j+1], rightIndex[j+1]]
                i -= 1
            else:
                op1 = ['insert', leftIndex[i+1], leftIndex[i+1], rightIndex[j], rightIndex[j+1]]
                j -= 1
        
        if op1[0] == op[0]:
            op[1] = op1[1]
            op[3] = op1[3]
        else:
            ops.append(op)
            op = op1
    
    # ops.append(op)
    ops.append(opStart)
    ops = list(ops)
    ops.reverse()

    # Console.write("Pre compression\n")
    # for op in ops:
    #     Console.write("%s %2d %2d %2d %2d '%s' '%s'\n" % (op[0], op[1], op[2], op[3], op[4], ''.join(leftArray[op[1]:op[2]]), ''.join(rightArray[op[3]:op[4]])))
    ops = CompressEdits(ops, leftArray, rightArray)

    return ops


def DoWhiteArray(text):
    result = []
    #  At some point I want to split whitespace with
    #  CR in them to multiple lines
    for right in re.split(r'([\s\xa0=]+)', text):
        if len(right) == 0:
            continue
        if right.isspace():
            lastCh = '*'
            for ch in right:
                if ch == ' ':
                    if lastCh != ' ':
                        result.append(ch)
                else:
                    result.append(ch)
                lastCh = ch
        else:
            result.append(right)
    return result

def CompressEdits(ops, leftArray, rightArray):
    opsNew = []
    left = None
    right = None

    for i in range(len(ops)):
        if ops[i][0] == 'remove':
            if leftArray[ops[i][1]][0] == '\n' and right != None:
                opsNew.append(right)
                right = None
            if left != None:
                left[2] = ops[i][2]
            else:
                left = ops[i]
        elif ops[i][0] == 'insert':
            if rightArray[ops[i][3]][0] == '\n' and left != None:
                opsNew.append(left)
                left = None
            if right != None:
                right[4] = ops[i][4]
            else:
                right = ops[i]
        else:
            if ops[i][2] - ops[i][1] == 1 and (leftArray[ops[i][1]] == ' ' or leftArray[ops[i][1]] == '\xa0') and \
                i+1 < len(ops) and ops[i+1][0] != 'equal' and not (left == None and right == None):
                if left != None:
                    left[2] = ops[i][2]
                else:
                    left = ['remove', ops[i][1], ops[i][2], ops[i][3], ops[i][4]]
                if right != None:
                    right[4] = ops[i][4]
                else:
                    right = ['insert', ops[i][1], ops[i][2], ops[i][3], ops[i][4]]
            else:
                if left != None:
                    opsNew.append(left)
                    left = None
                if right != None:
                    opsNew.append(right)
                    right = None
                opsNew.append(ops[i])


    if left != None:
        opsNew.append(left)
    if right != None:
        opsNew.append(right)

    return opsNew

if __name__ == '__main__':
    old = " attr1=\"value2\""
    new = " attr1=\"value1\""

    leftArray = DoWhiteArray(old)
    rightArray = DoWhiteArray(new)

    ops = ComputeEdits(leftArray, rightArray)

    for op in ops:
        Console.write("%s %2d %2d %2d %2d '%s' '%s'\n" % (op[0], op[1], op[2], op[3], op[4], ''.join(leftArray[op[1]:op[2]]), ''.join(rightArray[op[3]:op[4]])))

    Console.write("**********************************************\n")
    
    old = "This is\xa0a\xa0message\nwith one change"
    new = "This is\xa0a message with\ntwo change"
    leftArray = DoWhiteArray(old)
    rightArray = DoWhiteArray(new)

    ops = ComputeEdits(leftArray, rightArray)

    for op in ops:
        Console.write("%s %2d %2d %2d %2d '%s' '%s'\n" % (op[0], op[1], op[2], op[3], op[4], ''.join(leftArray[op[1]:op[2]]), ''.join(rightArray[op[3]:op[4]])))

    Console.write("**********************************************\n")

    old = "This document specifies algorithm identifiers and ASN.1 encoding formats for Elliptic Curve constructs using the curve25519 and curve448 curves. <!--\xa0Remove\xa0ph\n\xa0The\xa0signature\xa0algorithms\xa0covered\xa0are\xa0Ed25519,\xa0Ed25519ph,\xa0Ed448\xa0and\xa0Ed448ph.\n-->\nThe signature algorithms covered are Ed25519 and Ed448. The key agreement algorithm covered are X25519 and X448. The encoding for Public Key, Private Key and EdDSA digital signature structures is provided."
    
    new = "This document specifies algorithm identifiers and ASN.1 encoding formats for elliptic curve constructs using the curve25519 and curve448 curves.  The signature algorithms covered are Ed25519 and Ed448.  The key agreement algorithms covered are X25519 and X448.  The encoding for public key, private key, and Edwards-curve Digital Signature Algorithm (EdDSA) structures is provided."
    leftArray = DoWhiteArray(old)
    rightArray = DoWhiteArray(new)

    ops = ComputeEdits(leftArray, rightArray)

    for op in ops:
        Console.write("%s %2d %2d %2d %2d '%s' '%s'\n" % (op[0], op[1], op[2], op[3], op[4], ''.join(leftArray[op[1]:op[2]]), ''.join(rightArray[op[3]:op[4]])))

    Console.write("**********************************************\n")
    old = "The encoding for Public Key, Private Key and EdDSA digital signature structures is provided."
    new = "The encoding for public key, private key, and Edwards-curve Digital Signature Algorithm (EdDSA) structures is provided."
    leftArray = DoWhiteArray(old)
    rightArray = DoWhiteArray(new)

    ops = ComputeEdits(leftArray, rightArray)

    for op in ops:
        Console.write("%s %2d %2d %2d %2d '%s' '%s'\n" % (op[0], op[1], op[2], op[3], op[4], ''.join(leftArray[op[1]:op[2]]), ''.join(rightArray[op[3]:op[4]])))

    Console.write("**********************************************\n")

    old = "In <xref target=\"RFC8032\"/> the elliptic curve signature system Edwards-curve Digital Signature Algorithm (EdDSA) is described along with a recommendation for the use of the curve25519 and curve448. EdDSA has defined two modes, the PureEdDSA mode without pre-hashing, and the HashEdDSA mode with pre-hashing.\n<!--\xa0Remove\xa0pre-hash\nThe\xa0Ed25519ph\xa0and\xa0Ed448ph\xa0algorithm\xa0definitions\xa0specify\xa0the\xa0one-way\xa0hash\xa0function\xa0that\xa0is\xa0used\xa0for\xa0pre-hashing.\nThe\xa0convention\xa0used\xa0for\xa0identifying\xa0the\xa0algorithm/curve\xa0combinations\xa0are\xa0to\xa0use\xa0the\xa0Ed25519\xa0and\xa0Ed448\xa0for\xa0the\xa0PureEdDSA\xa0mode,\xa0with\xa0Ed25519ph\xa0and\xa0Ed448ph\xa0for\xa0the\xa0HashEdDSA\xa0mode.\n-->\nThe convention used for identifying the algorithm/curve combinations is to use \"Ed25519\" and \"Ed448\" for the PureEdDSA mode. The document does not provide the conventions needed for the pre-hash versions of the signature algorithm. The use of the OIDs is described for public keys, private keys and signatures."
    new = "In <xref target=\"RFC8032\"/> the elliptic curve signature system Edwards-curve Digital Signature Algorithm (EdDSA) is described along with a recommendation for the use of the curve25519 and curve448.  EdDSA has defined two modes: the PureEdDSA mode without prehashing and the HashEdDSA mode with prehashing.  The convention used for identifying the algorithm/curve combinations is to use \"Ed25519\" and \"Ed448\" for the PureEdDSA mode.  This document does not provide the conventions needed for the prehash versions of the signature algorithm.  The use of the OIDs is described for public keys, private keys and signatures."

    leftArray = DoWhiteArray(old)
    rightArray = DoWhiteArray(new)
    ops = ComputeEdits(leftArray, rightArray)
    for op in ops:
        Console.write("%s %2d %2d %2d %2d '%s' '%s'\n" % (op[0], op[1], op[2], op[3], op[4], ''.join(leftArray[op[1]:op[2]]), ''.join(rightArray[op[3]:op[4]])))
