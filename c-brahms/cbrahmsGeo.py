"""
Algorithms P1, P2 and P3 are described in the following publication:

Ukkonen, Esko; Lemstrom, Kjell; Makinen, Veli:
Geometric algorithms for transposition invariant content-based music retrieval.
in Proc. 4th International Conference on Music Information Retrieval, pp. 193-199, 2003.
https://tuhat.halvi.helsinki.fi/portal/services/downloadRegister/14287445/03ISMIR_ULM.pdf

In addition to Ukkonen's paper, we follow a ruby implementation by Mika Turkia, found at https://github.com/turkia/geometric-mir-algorithms/blob/master/lib/mir.rb
"""

import midiparser

"""
class horizontalLineSegments:
    data_set = []

    def __init__(self, segments):
        self.data_set = segments
"""

"""
A custom comparator to order horizontal line segments from left to right, and then bottom to top.
def cmp2Dvectors(l1, l2):
    Input: two horizontal line segments
    Output: -1, 0, or 1 if l1 is less than, equal to, or greater than l2
    if ((l1[0] < l2[0]) or (l1[0] == l2[0] and l1[1] < l2[1])):
        return -1
    elif ((l1[0] == l2[0]) and (l1[1] == l2[1])):
        return 0
    else:
        return 1
"""

def sub_2D_vectors(l1, l2):
    """
    Input: two vectors in R^2
    Output: the difference between them. i.e., the vector f such that l1 + f = l2
    """
    x_diff = l2[0] - l1[0]
    y_diff = l2[1] - l1[0]
    return (x_diff, y_diff)

def add_2D_vectors(l1, f):
    """
    Input: a horizontal line segment, and a 2-d function
    Output: a horizontal line segment shifted by the 2-d function
    """
    l1[0] += f[0]
    l1[1] += f[1]
    return l1

# An exact matching algorithm 
def P1(pattern, source):
    """
    Input: two lists of horizontal line segments. One is the 'pattern', which we are looking for in the larger 'source'
    Output: all horizontal / vertical line segment shifts which shift the pattern into some exact match within the source
    """
    shift_matches = []

    # q_i pointers, one for each segment in the pattern 
    ptrs = [(float("-inf"), float("-inf")) for i in range(len(pattern))]
    prts.append((float("inf"), float("inf")))

    # there are n-m possible matches, one for each possible match of p_1
    for t in range(len(source)-len(pattern)):
        # Compute the shift to match p_1 and t_j
        shift = sub2Dvectors(query[0], source[t])

        # For each pattern segment other than the first, look for an exact match in the source
        for p in range(1, len(query)):
            # p+t comes from Mika. It is the first possible match for p. This line implements next(q_i).
            possible_match = p+t
            ptrs[p] = max(ptrs[p], source[t])

            # look through the sorted source list for a match of this particular pattern segment
            while ptrs[p] < add2Dvectors(pattern[p], shift):
                # q_i <- next(q_i)
                possible_match += 1
                ptrs[p] = source[possible_match]
            # Check if there is no match for this p
            if ptrs[p] == add2Dvectors(pattern[p], shift):
                break
            if p == len(pattern)+1:
               shift_matches.append(shift)





#shift = [source[j][z] - query[0][z] for z in range(len(source[j]))]
