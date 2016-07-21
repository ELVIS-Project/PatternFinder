"""
Algorithms P1, P2 and P3 are described in the following publication:

Ukkonen, Esko; Lemstrom, Kjell; Makinen, Veli:
Geometric algorithms for transposition invariant content-based music retrieval.
in Proc. 4th International Conference on Music Information Retrieval, pp. 193-199, 2003.
https://tuhat.halvi.helsinki.fi/portal/services/downloadRegister/14287445/03ISMIR_ULM.pdf

In addition to Ukkonen's paper, we follow a ruby implementation by Mika Turkia, found at https://github.com/turkia/geometric-mir-algorithms/blob/master/lib/mir.rb
"""

import midiparser

def sub_2D_vectors(l1, l2):
    """
    Input: two vectors in R^2
    Output: the difference between them. i.e., the vector f such that l1 + f = l2
    """
    x_diff = l2[0] - l1[0]
    y_diff = l2[1] - l1[1]
    return [x_diff, y_diff]

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
    pattern.sort()
    source.sort()

    # q_i pointers, one for each segment in the pattern 
    ptrs = [[float("-inf"), float("-inf")] for i in range(len(pattern))]
    ptrs.append([float("inf"), float("inf")])

    # there are n-m+1 possible matches, one for each possible match of p_0
    for t in range(len(source) - len(pattern) + 1):
        # Compute the shift to match p_1 and t_j
        shift = sub_2D_vectors(list(pattern[0]), source[t])

        # For each pattern segment other than the first, look for an exact match in the source
        for p in range(1, len(pattern)):
            ### q_i <- next(q_i) : start attempting to match p_i with the match of p_0; this implies that two notes in unison could match to the same single note in the source.
            possible_match = p + t - 1
            ptrs[p] = max(ptrs[p], source[t])

            # look through the sorted source list for a match of this particular pattern segment
            while ptrs[p] < add_2D_vectors(list(pattern[p]), shift):
                possible_match += 1
                # Avoid index out of bounds
                if possible_match == len(source):
                    break
                ### q_i <- next(q_i)
                ptrs[p] = source[possible_match]
            # Check if there is no match for this p_i. If so, there is no exact match for this t. Break, and try the next one.
            if ptrs[p] > add_2D_vectors(list(pattern[p]), shift):
                break
            # Check if we have successfully matched all notes in the pattern
            if p == len(pattern)-1:
               shift_matches.append(shift)
 
    return shift_matches





#shift = [source[j][z] - query[0][z] for z in range(len(source[j]))]
