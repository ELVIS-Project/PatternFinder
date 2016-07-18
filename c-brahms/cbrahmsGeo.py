#!/usr/local/bin/python3

"""
Algorithms P1, P2 and P3 are described in the following publication:

Ukkonen, Esko; Lemstrom, Kjell; Makinen, Veli:
Geometric algorithms for transposition invariant content-based music retrieval.
in Proc. 4th International Conference on Music Information Retrieval, pp. 193-199, 2003.
https://tuhat.halvi.helsinki.fi/portal/services/downloadRegister/14287445/03ISMIR_ULM.pdf

In addition to Ukkonen's paper, we follow a ruby implementation by Mika Turkia, found at https://github.com/turkia/geometric-mir-algorithms/blob/master/lib/mir.rb
"""

inf = float("inf")
-inf = float("-inf")

# A custom comparator to order horizontal line segments from left to right, and then bottom to top.
def cmpSegments(ralph, larry):
    """
    Input: two horizontal line segments
    Output: -1, 0, or 1 if ralph is less than, equal to, or greater than larry
    """
    if ((ralph[0] < larry[0]) or (ralph[0] == larry[0] and ralph[1] < larry[1])):
        return -1
    else if ((ralph[0] == larry[0]) and (ralph[1] == larry[1])):
        return 0
    else
        return 1



# Sample input pattern: Over the Rainbow melody
P = []


