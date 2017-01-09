"""
Algorithms P1, P2 and P3 are described in the following publication:

Ukkonen, Esko; Lemstrom, Kjell; Makinen, Veli:
Geometric algorithms for transposition invariant content-based music retrieval.
in Proc. 4th International Conference on Music Information Retrieval, pp. 193-199, 2003.
https://tuhat.halvi.helsinki.fi/portal/services/downloadRegister/14287445/03ISMIR_ULM.pdf

In addition to Ukkonen's paper, we follow a ruby implementation by Mika Turkia, found at https://github.com/turkia/geometric-mir-algorithms/blob/master/lib/mir.rb
"""

from LineSegment import LineSegment, TurningPoint, TwoDVector
import itertools
import midiparser
import Queue
import copy
import pdb

def sub_2D_vectors(l1, l2):
    """
    Input: two vectors in R^2
    Output: the difference between them. i.e., the vector f such that l1 + f = l2
    """
    return [l2[0]-l1[0], l2[1]-l1[1]]

def add_2D_vectors(l1, f):
    """
    Input: a horizontal line segment, and a 2-d function
    Output: a horizontal line segment shifted by the 2-d function
    """
    return [l1[0] + f[0], l1[1] + f[1]]

# An exact matching algorithm 
def P1(pattern, source, option = None):
    """
    Input: two lists of horizontal line segments. One is the 'pattern', which we are looking for in the 'source'
    Output: all 2-D line segment shifts which shift the pattern into some exact match within the source. If the pattern is larger than the source, P1 should return an empty list.

    Note: triple-pound comments (###) reference Ukkonen's pseudocode.
    """
    # Make copies of pattern, source to avoid altering the data
    pattern = copy.deepcopy(pattern) # of size m
    source = copy.deepcopy(source) # of size n

    # Lexicographically sort the pattern and source
    pattern.sort()
    source.sort()

    # Store Results
    shift_matches = []

    # A list of pointers referred to as "q_i". There is one for each pattern line segment p_i. q_i pointers refer to a possible match between p_i and a segment in the source called s_j.
    ptrs = [0 for p in pattern]

    ### (1) for j <- 1, ..., n-m do
    # Any solution to the P1 specification must at least match p_0 with a segment in source. So we loop through all possible matches for p_0, and ascertain whether any of the resulting shifts also induce a total match for the whole pattern. There are n - m + 1 possible matches (the pseudocode appears to have missed the + 1).
    for t in range(len(source) - len(pattern) + 1):
        # Compute the shift to match p_0 and s_j.
        shift = source[t] - pattern[0]

        ### (3) for j <- 1, ..., n - m do
        # Find exact matches for p_1, ..., p_m
        for p in range(1, len(pattern)):
            ### (8) q_i <- max(q_i, t_j)
            # The first value for q_i is either its offset from the match of p_0 (s_j), or its previous value from the last iteration. We take the maximum because q_i is non-decreasing.
            # p + t will never be greater than len(source).
            # the choice of p + t as a minimum possible match for p_i implies that two unison voices in the pattern cannot match to a single voice in the source. Every note in the pattern must have a unique matching note in the source.
            ptrs[p] = max(ptrs[p], p + t)

            ### (9) while q_i < p_i + f
            while source[ptrs[p]] < pattern[p] + shift and ptrs[p] + 1 < len(source):
                ### (9) q_i <- next(q_i)
                ptrs[p] += 1

            ### (10) until q_i > p_i + f
            # Check if there is no match for this p_i. If so, there is no exact match for this t_j. Break, and try the next one.
            if option == 'onset':
                if source[ptrs[p]] != pattern[p] + shift: break
            elif option == 'segment':
                if source[ptrs[p]] != pattern[p] + shift or source[ptrs[p]].duration != pattern[p].duration: break

            ### (11) if i = m + 1 then output(f)
            # Check if we have successfully matched all notes in the pattern
            if p == len(pattern)-1:
                shift_matches.append(shift)

    return shift_matches

# Largest Common Subset matching algorithm
def P2(pattern, source, option = None):
    """
    Input: two lists of horizontal line segments. One is the 'pattern', which we are looking for in the larger 'source'
    Output: all horizontal / vertical line segment shifts which shift the pattern so that it shares a subset with the source

    The # of mismatches between source and pattern is defined as len(pattern) - # of matches between pattern and source.
    """
    pattern = copy.deepcopy(pattern)
    source = copy.deepcopy(source)
    source.append(LineSegment([float("inf"), 0, float("inf")]))
    # Lexicographically sort the pattern and source
    pattern.sort()
    source.sort()

    # Priority queue of shifts
    shifts = Queue.PriorityQueue(len(pattern) * len(source))
    # Current minimum shift
    shift_candidate = TwoDVector(float("-inf"), float("-inf"))
    # Multiplicity counter for each distinct shift
    c = 0
    # Results
    shift_matches = []

    # Pointers which refer to source INDICES. q_i points to s_i, a potential match for p_i
    q = [0 for s in range(len(pattern))]

    # Fill the priority queue 
    for i in range(len(pattern)):
        # priority queue members are tuples:
        #   1) f_i = s_{q_i} - p_i ;;; the shift which brings ith pattern to the q_ith source 
        #   2) i ;;; the index of this pattern element
        shifts.put([source[q[i]] - pattern[i], i])

    while(shift_candidate < TwoDVector(float("inf"), float("inf"))):
        ## min(F)
        min_shift = shifts.get()
        # index of the pattern p_i which corresponds to this minimum shift
        p_i = min_shift[1]
        ## update(F): q_i <- next(q_i), and put the new translation into the pq
        q[p_i] += 1

        if q[p_i] < len(source):
            #Optionally, here we can check for duration match as well
            shifts.put([source[q[p_i]] - pattern[p_i], p_i])

        ## Keep count
        if shift_candidate == min_shift[0]:
            c += 1
        else:
            if shift_candidate != TwoDVector(float("-inf"), float("-inf")):
                # Save shift candidates with their multiplicity
                shift_matches.append([shift_candidate, c])
            shift_candidate = min_shift[0]
            c = 1

    # Return all possible shifts and their multiplicities
    if option == "all":
        return shift_matches
    else:
        # Return shifts only with 'option' number of mismatches
        try:
            option = int(option)
        # Default: minimize the mismatches
        except TypeError:
            option = len(pattern) - max(zip(*shift_matches)[1])

    # Return shifts with the given mismatch
    return [shift[0] for shift in shift_matches if shift[1] == len(pattern) - option] # number of mismatches is relative to the length of the pattern (not the length of the source).


def P3(pattern, source, option):
    """
    Input: two lists of horizontal line segments. One is the 'pattern', which we are looking for in the larger 'source'
    Output: all shifts which result in the largest intersection (measured in length) between the two sets of line segments
    """
    #curiosities: Not sure a negative (leftwards) match is possible with this algorithm (i.e., just a suffix of the pattern matches the beginning of the source). think about it?

    # Currently, midi parser outputs a list of [onset, note, offset] so that P1, P2 keep working
    # Eventually the algorithms should take line segment set objects as input, but for now..
    pattern = [LineSegment(p[0], p[2], p[2] - p[0], p[1]) for p in pattern]
    source = [LineSegment(s[0], s[2], s[2] - s[0], s[1]) for s in source]

    # Keep track of C_h for each y-coordinate in 256 buckets, which corresponds to every possible MIDI value
    # Negative indices will wrap around; we assume all vertical translations are between -128 and 128
    vertical_translations = [{'value' : 0, 'slope' : 0, 'prev_turning_point' : 0} for i in range(256)]
    # Store 4 * m turning points in a priority queue
    pq_size = 4 * len(pattern)
    translations = Queue.PriorityQueue(pq_size)
    # Keep track of the longest intersection
    best = 0
    list_of_shifts = []

    # Populate the priority queue with all 4 types of pointers
    for p in pattern:
        for t in range(4):
            ralph = TurningPoint(p, source[0], 0, t)
            translations.put(ralph)

    # All 4 * m turning points now traverse the source
    for i in range(pq_size * len(source)):
        min_translation = translations.get()

        # Increment the cumulative intersection value for this y-coordinate translation
        # min_translation.y is a MIDI pitch: it should be a whole number, and can be casted to int
        vertical_translations[int(min_translation.y)]['value'] += \
            (vertical_translations[int(min_translation.y)]['slope']
            * (min_translation.value - vertical_translations[int(min_translation.y)]['prev_turning_point']))
        # save the TURNING POINT value, not the segment translation distance.
        vertical_translations[int(min_translation.y)]['prev_turning_point'] = min_translation.value
        # TODO store prev_turning_point as a turning point object, not as just the x coord?

        # Keep track of best matches
        if vertical_translations[int(min_translation.y)]['value'] > best:
            list_of_shifts = []
            best = vertical_translations[int(min_translation.y)]['value']
        # Append a translation if it hasn't been added already
        if vertical_translations[int(min_translation.y)]['value'] >= best and min_translation.vector not in list_of_shifts:
            # Append the distance between the two segments, measured from their onset times.
            # TODO you don't want to append the dsitance measured by onset times; you want to append the distances based on the turning point values. we are measuring total INTERSECTION, it can be only at the 4 turning points that the intersection is the highest!
            list_of_shifts.append(min_translation.vector)

        # Update slope
        if min_translation.type in [0, 3]:
            vertical_translations[int(min_translation.y)]['slope'] += 1
        else:
            vertical_translations[int(min_translation.y)]['slope'] -= 1

        # Update pointer
        if min_translation.source_index < len(source) - 1:
           translations.put(TurningPoint(min_translation.pattern_segment, source[min_translation.source_index + 1], min_translation.source_index + 1, min_translation.type))

    return list_of_shifts
