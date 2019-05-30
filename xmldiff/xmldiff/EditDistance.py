import re
import sys
import six

if six.PY2:
    from aenum import Enum
else:
    from enum import Enum

Console = sys.stdout


class Trace(Enum):
    STOP = 1
    DIAG = 2
    UP = 3
    LEFT = 4


def matrix(left, right):
    if left == right:
        if left[0] == ' ':
            return (0, 2)
        return (0, 1)
    if '\n' in left:
        if '\n' in right:
            return (1, 8)
        return (1, -200)
    elif '\n' in right:
        return (1, -200)
    return (1, -100)


def ComputeEdits(leftArray, rightArray):

    trace = {}
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

    leftIndex = [i for i in range(rangeStart, len(leftArray)-rangeEnd)]
    rightIndex = [i for i in range(rangeStart, len(rightArray)-rangeEnd)]
    # leftIndex = [ i for i in range(rangeStart, len(leftArray)-rangeEnd)
    #               if leftArray[i] != ' ' ]
    # rightIndex = [ i for i in range(rangeStart, len(rightArray)-rangeEnd)
    #                if rightArray[i] != ' ' ]
    leftIndex.insert(0, 0)
    rightIndex.insert(0, 0)

    S = len(leftIndex)
    T = len(rightIndex)

    gap = 10
    o = gap   # gap
    e = 3     # extend
    maxNegValue = - 655465

    v = {}
    vDiagonal = 0    # best score in cell
    f = maxNegValue  # score from diagonal
    h = maxNegValue  # best score ending with gap from left
    g = {}           # best score ending with gap from above
    g[0] = f
    for i in range(1, T):
        v[i] = -o - (i-1)*e
        g[i] = maxNegValue

    lengthOfHorizontalGap = 0
    lengthOfVerticalGap = {}

    maximumScore = maxNegValue

    trace[0, 0] = Trace.STOP
    for i in range(1, S):
        trace[i, 0] = Trace.UP

    for i in range(1, T):
        trace[0, i] = Trace.LEFT

    #  Fill in the matrices
    for i in range(1, S):   # for all rows
        v[0] = -o - (i - 1) * e

        # Console.write(str(i))
        # Console.write(": \n")
        left = leftArray[leftIndex[i]]

        for j in range(1, T):  # for all columns
            right = rightArray[rightIndex[j]]

            simularityScore = matrix(left, right)

            f = vDiagonal + simularityScore[1]

            # which cell from the left?
            if h - e >= v[j-1] - o:
                h -= e
                lengthOfHorizontalGap += simularityScore[0]
            else:
                h = v[j-1] - o
                lengthOfHorizontalGap = 1

            # which cell from above?
            if g[j] - e >= v[j] - o:
                g[j] = g[j] - e
                lengthOfVerticalGap[j] = lengthOfVerticalGap[j] + simularityScore[0]
            else:
                g[j] = v[j] - o
                lengthOfVerticalGap[j] = 1

            vDiagonal = v[j]
            v[j] = max(f, g[j], h)  # get best score
            if v[j] > maximumScore:
                maximumScore = v[j]

            if v[j] == f:
                trace[i, j] = Trace.DIAG
            elif v[j] == g[j]:
                trace[i, j] = Trace.UP
                # lengths[l] = lengthOfVerticalGap[j]
            else:
                trace[i, j] = Trace.LEFT
                # lengths[l] = lengthOfHorizontalGap

        # PrintLine(i, T, v, g, lengthOfVerticalGap, trace)

        # Reset
        h = maxNegValue
        vDiagonal = 0
        lengthOfHorizontalGap = 0
        # Console.write("\n")

    # Console.write("\n")
    # for i in range(S):
    #    Console.write(str(i))
    #    Console.write(": ")
    #    for j in range(T):
    #        if trace[i,j] == Trace.LEFT:
    #            Console.write('L')
    #        elif trace[i,j] == Trace.UP:
    #            Console.write('U')
    #        elif trace[i,j] == Trace.DIAG:
    #            Console.write('D')
    #        elif trace[i,j] == Trace.STOP:
    #            Console.write('S')
    #        else:
    #            Console.write('X')
    #        Console.write(" ")
    #    Console.write("\n")

    i = S - 1
    j = T - 1

    # val = d[i, j]
    ops = []
    leftIndex.append(leftIndex[-1]+1)
    rightIndex.append(rightIndex[-1]+1)
    ops = []

    op = opEnd
    op2 = None

    stillGoing = True
    while stillGoing:
        if trace[i, j] == Trace.UP:
            op1 = ['remove', leftIndex[i], leftIndex[i+1], rightIndex[j+1], rightIndex[j+1]]
            i -= 1
        elif trace[i, j] == Trace.LEFT:
            op1 = ['insert', leftIndex[i+1], leftIndex[i+1], rightIndex[j], rightIndex[j+1]]
            j -= 1
        elif trace[i, j] == Trace.DIAG:
            if leftArray[leftIndex[i]] == rightArray[rightIndex[j]]:
                op1 = ['equal', leftIndex[i], leftIndex[i+1], rightIndex[j], rightIndex[j+1]]
            else:
                op1 = ['remove', leftIndex[i], leftIndex[i+1], rightIndex[j+1], rightIndex[j+1]]
                op2 = ['insert', leftIndex[i+1],  leftIndex[i+1], rightIndex[j], rightIndex[j+1]]
            i -= 1
            j -= 1
        else:
            stillGoing = False
            ops.append(op)
            break

        if op2:
            if op2[0] == op[0]:
                op[1] = op2[1]
                op[3] = op2[3]
            elif op1[0] == op[0]:
                op[1] = op1[1]
                op[3] = op1[3]
                op1 = op2
            else:
                ops.append(op2)
                op = op2
            op2 = None

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
    #     Console.write("%s %2d %2d %2d %2d '%s' '%s'\n" % (op[0], op[1], op[2], op[3], op[4],
    #           ''.join(leftArray[op[1]:op[2]]), ''.join(rightArray[op[3]:op[4]])))
    ops = CompressEdits(ops, leftArray, rightArray)

    return ops


def PrintLine(i, T, v, g, lengthOfVerticalGap, trace):
    Console.write("i={0:3d}".format(i))
    for j in range(1, T):
        Console.write("{0:3d} ".format(v[j]))
    Console.write("\n")

    for j in range(1, T):
        Console.write("{0:3d} ".format(g[j]))
    Console.write("\n")

    for j in range(1, T):
        Console.write("{0:3d} ".format(lengthOfVerticalGap[j]))
    Console.write("\n")

    for j in range(1, T):
        if trace[i, j] == Trace.LEFT:
            ch = 'L'
        elif trace[i, j] == Trace.UP:
            ch = 'U'
        elif trace[i, j] == Trace.DIAG:
            ch = 'D'
        elif trace[i, j] == Trace.STOP:
            ch = 'S'
        else:
            ch = ' '
        Console.write("  {0} ".format(ch))
    Console.write("\n")

    Console.write("\n")


def DoWhiteArray(text):
    result = []
    #  At some point I want to split whitespace with
    #  CR in them to multiple lines
    for right in re.split(r'([\s\xa0=]+)', text, flags=re.UNICODE):
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
            if leftArray[ops[i][1]][0] == '\n' and right is not None:
                opsNew.append(right)
                right = None
            if left is not None:
                left[2] = ops[i][2]
            else:
                left = ops[i]
        elif ops[i][0] == 'insert':
            if rightArray[ops[i][3]][0] == '\n' and left is not None:
                opsNew.append(left)
                left = None
            if right is not None:
                right[4] = ops[i][4]
            else:
                right = ops[i]
        else:
            if ops[i][2] - ops[i][1] == 1 and \
               (leftArray[ops[i][1]] == u' ' or leftArray[ops[i][1]] == u'\xa0') and \
               i+1 < len(ops) and ops[i+1][0] != 'equal' and not (left is None and right is None):
                if left is not None:
                    left[2] = ops[i][2]
                else:
                    left = ['remove', ops[i][1], ops[i][2], ops[i][3], ops[i][4]]
                if right is not None:
                    right[4] = ops[i][4]
                else:
                    right = ['insert', ops[i][1], ops[i][2], ops[i][3], ops[i][4]]
            else:
                if left is not None:
                    opsNew.append(left)
                    left = None
                if right is not None:
                    opsNew.append(right)
                    right = None
                opsNew.append(ops[i])

    if left is not None:
        opsNew.append(left)
    if right is not None:
        opsNew.append(right)

    return opsNew


if __name__ == '__main__':
    old = " attr1=\"value2\""
    new = " attr1=\"value1\""

    leftArray = DoWhiteArray(old)
    rightArray = DoWhiteArray(new)

    ops = ComputeEdits(leftArray, rightArray)

    for op in ops:
        Console.write("%s %2d %2d %2d %2d '%s' '%s'\n" %
                      (op[0], op[1], op[2], op[3], op[4],
                       ''.join(leftArray[op[1]:op[2]]), ''.join(rightArray[op[3]:op[4]])))

    Console.write("**********************************************\n")

    old = "This is\xa0a\xa0message\nwith one change"
    new = "This is\xa0a message with\ntwo change"
    leftArray = DoWhiteArray(old)
    rightArray = DoWhiteArray(new)

    ops = ComputeEdits(leftArray, rightArray)

    for op in ops:
        Console.write("%s %2d %2d %2d %2d '%s' '%s'\n" %
                      (op[0], op[1], op[2], op[3], op[4],
                       ''.join(leftArray[op[1]:op[2]]), ''.join(rightArray[op[3]:op[4]])))

    Console.write("**********************************************\n")

    old = "This document specifies Elliptic Curve constructs using the curve25519"
    new = "This document specifies elliptic curve constructs using the curve25519"
    leftArray = DoWhiteArray(old)
    rightArray = DoWhiteArray(new)

    ops = ComputeEdits(leftArray, rightArray)

    for op in ops:
        Console.write("%s %2d %2d %2d %2d '%s' '%s'\n" %
                      (op[0], op[1], op[2], op[3], op[4], ''.join(leftArray[op[1]:op[2]]),
                       ''.join(rightArray[op[3]:op[4]])))

    Console.write("**********************************************\n")

    old = "This document specifies algorithm identifiers and ASN.1 encoding formats for " + \
          "Elliptic Curve constructs using the curve25519 and curve448 curves. <!--\xa0" + \
          "Remove\xa0ph\n\xa0The\xa0signature\xa0algorithms\xa0covered\xa0are\xa0Ed25519," + \
          "\xa0Ed25519ph,\xa0Ed448\xa0and\xa0Ed448ph.\n-->\nThe signature algorithms covered" + \
          " are Ed25519 and Ed448. The key agreement algorithm covered are X25519 and X448." + \
          " The encoding for Public Key, Private Key and EdDSA digital signature structures " + \
          "is provided."

    new = "This document specifies algorithm identifiers and ASN.1 encoding formats for " + \
          "elliptic curve constructs using the curve25519 and curve448 curves.  The signature " + \
          "algorithms covered are Ed25519 and Ed448.  The key agreement algorithms covered are " + \
          "X25519 and X448.  The encoding for public key, private key, and Edwards-curve" + \
          " Digital Signature Algorithm (EdDSA) structures is provided."

    leftArray = DoWhiteArray(old)
    rightArray = DoWhiteArray(new)

    ops = ComputeEdits(leftArray, rightArray)

    for op in ops:
        Console.write("%s %2d %2d %2d %2d '%s' '%s'\n" %
                      (op[0], op[1], op[2], op[3], op[4],
                       ''.join(leftArray[op[1]:op[2]]), ''.join(rightArray[op[3]:op[4]])))

    Console.write("**********************************************\n")
    old = "The encoding for Public Key, Private Key and EdDSA digital signature structures " + \
          "is provided."
    new = "The encoding for public key, private key, and Edwards-curve Digital Signature " + \
          "Algorithm (EdDSA) structures is provided."
    leftArray = DoWhiteArray(old)
    rightArray = DoWhiteArray(new)

    ops = ComputeEdits(leftArray, rightArray)

    for op in ops:
        Console.write("%s %2d %2d %2d %2d '%s' '%s'\n" %
                      (op[0], op[1], op[2], op[3], op[4],
                       ''.join(leftArray[op[1]:op[2]]), ''.join(rightArray[op[3]:op[4]])))

    Console.write("**********************************************\n")

    old = "In <xref target=\"RFC8032\"/> the elliptic curve signature system Edwards-curve " + \
          "Digital Signature Algorithm (EdDSA) is described along with a recommendation for " + \
          "the use of the curve25519 and curve448. EdDSA has defined two modes, the PureEdDSA " + \
          "mode without pre-hashing, and the HashEdDSA mode with pre-hashing.\n<!--\xa0Remove" + \
          "\xa0pre-hash\nThe\xa0Ed25519ph\xa0and\xa0Ed448ph\xa0algorithm\xa0definitions\xa0s" + \
          "pecify\xa0the\xa0one-way\xa0hash\xa0function\xa0that\xa0is\xa0used\xa0for\xa0pre-" + \
          "hashing.\nThe\xa0convention\xa0used\xa0for\xa0identifying\xa0the\xa0algorithm/curve" + \
          "\xa0combinations\xa0are\xa0to\xa0use\xa0the\xa0Ed25519\xa0and\xa0Ed448\xa0for\xa0the" + \
          "\xa0PureEdDSA\xa0mode,\xa0with\xa0Ed25519ph\xa0and\xa0Ed448ph\xa0for\xa0the\xa0" + \
          "HashEdDSA\xa0mode.\n-->\nThe convention used for identifying the algorithm/curve " + \
          "combinations is to use \"Ed25519\" and \"Ed448\" for the PureEdDSA mode. The " + \
          "document " + \
          "does not provide the conventions needed for the pre-hash versions of the signature " + \
          "algorithm. The use of the OIDs is described for public keys, private keys and " + \
          "signatures."
    new = "In <xref target=\"RFC8032\"/> the elliptic curve signature system Edwards-curve " + \
          "Digital Signature Algorithm (EdDSA) is described along with a recommendation for " + \
          "the use of the curve25519 and curve448.  EdDSA has defined two modes: the PureEdDSA " + \
          "mode without prehashing and the HashEdDSA mode with prehashing.  The convention " + \
          "used for identifying the algorithm/curve combinations is to use \"Ed25519\" and " + \
          "\"Ed448\" for the PureEdDSA mode.  This document does not provide the conventions " + \
          "needed for the prehash versions of the signature algorithm.  The use of the OIDs is " + \
          "described for public keys, private keys and signatures."

    leftArray = DoWhiteArray(old)
    rightArray = DoWhiteArray(new)
    ops = ComputeEdits(leftArray, rightArray)
    for op in ops:
        Console.write("%s %2d %2d %2d %2d '%s' '%s'\n" %
                      (op[0], op[1], op[2], op[3], op[4],
                       ''.join(leftArray[op[1]:op[2]]), ''.join(rightArray[op[3]:op[4]])))
