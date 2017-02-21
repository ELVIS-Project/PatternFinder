"""
Algorithms P1, P2 and P3 are described in the following publication:

Ukkonen, Esko; Lemstrom, Kjell; Makinen, Veli:
Geometric algorithms for transposition invariant content-based music retrieval.
in Proc. 4th International Conference on Music Information Retrieval, pp. 193-199, 2003.
https://tuhat.halvi.helsinki.fi/portal/services/downloadRegister/14287445/03ISMIR_ULM.pdf

In addition to Ukkonen's paper, we follow a ruby implementation by Mika Turkia, found at https://github.com/turkia/geometric-mir-algorithms/blob/master/lib/mir.rb
"""

from LineSegment import LineSegment, LineSegmentSet, TurningPoint, TwoDVector, Bucket
import itertools
import midiparser
import Queue
import copy
import pdb

# An exact matching algorithm 
def P1(pattern, source, option = None):
    """
    Input: two lists of horizontal line segments. One is the 'pattern', which we are looking for in the 'source'
    Output: all 2-D line segment shifts which shift the pattern into some exact match within the source. If the pattern is larger than the source, P1 should return an empty list.

    Note: triple-pound comments (###) reference Ukkonen's pseudocode.

    POLYPHONIC BEHAVIOUR:
        P1 can find exact melodic occurrences through many voices. It will only find multiple matches if the first note of the pattern can match more than one identical note in the source, while all the rest of the notes find possibly non-unique matches. THIS should be changed.
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
    # Any solution to the P1 specification must at least match p_0 with a segment in source. So we loop through all possible matches for p_0, and ascertain whether any of the resulting shifts also induce a total match for the whole pattern. There are n - m + 1 possible matches (the pseudocode in the paper appears to have missed the + 1).
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
            if option == 'segment':
                if source[ptrs[p]] != pattern[p] + shift or source[ptrs[p]].duration != pattern[p].duration: break
            else: # or if option == 'onset':
                if source[ptrs[p]] != pattern[p] + shift: break

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
    source.append(LineSegment(float("inf"), float("inf"), 0))
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
    # number of mismatches is relative to the length of the pattern (not the length of the source).
    return [shift[0] for shift in shift_matches if shift[1] == len(pattern) - option]

def P3(pattern, source, option = None):
    """
    Input: two lists of horizontal line segments. One is the 'pattern', which we are looking for in the larger 'source'
    Output: all shifts which result in the largest intersection (measured in length) between the two sets of line segments

    Only checks for transpositions within -127 and 127 semitones.
    """
    #curiosities: Not sure a negative (leftwards) match is possible with this algorithm (i.e., just a suffix of the pattern matches the beginning of the source). think about it?
    # Sanity check: Each bucket represents a SLOPE and a TALLY for every y value. 
    # There are four turning points per pattern segment. Each pattern segment can influence the n tally (there are as many tallys as there are vertical translations) in four ways! We sort them all and go through it one at a time.

    # Sort pattern and source
    #pattern = LineSegmentSet(pattern)
    source = LineSegmentSet(source)
    #pattern.onset_sort = sorted(pattern)

    # Remove overlapping of segments
    if option == "overlap":
        pass
    else:
        # Merging overlaps depends on previously being sorted.
        source.mergeOverlappingSegments()
        source.mergeOverlappingSegments()

    pattern.sort()
    source_onset_sort = sorted(source, key = lambda x: (x.onset, x.pitch))
    source_offset_sort = sorted(source, key = lambda x: (x.offset, x.pitch))

        #helper = source_onset_sort[1:]
        #source_onset_sort.append(None)
        #source_no_overlap = [mergeTwoSegments(elt[0], elt[1]) if elt[0].doesOverlapWith(elt[1]) else elt[0] for elt in zip(source_onset_sort, helper)]


    # All vertical translations are between -127 and 127 since there are 127 possible MIDI values.
    # So, we need a total of (127*2 + 1) = 255 buckets to keep track of each C_h.
    # Negative indices will wrap around. 
    # Initial prev_tp does not matter since slope is zero
    C_h = [Bucket(value=0, slope=0, prev_tp=TwoDVector(0, 0)) for i in range(256)]

    # Store 4 * m turning points in a priority queue (4 types per pattern segment)
    turning_points = Queue.PriorityQueue(4 * len(pattern))
    for p in pattern:
        turning_points.put(TurningPoint(p, source_onset_sort[0], 0, 0))
        turning_points.put(TurningPoint(p, source_onset_sort[0], 0, 1))
        turning_points.put(TurningPoint(p, source_offset_sort[0], 0, 2))
        turning_points.put(TurningPoint(p, source_offset_sort[0], 0, 3))

    # Keep track of the longest intersection
    best = 0
    list_of_shifts = []

    # LOOP: All 4 * m turning points now traverse the source. types 0,1 traverse onsets, and types 2,3 traverse offsets.
    for i in range(4 * len(pattern) * len(source)):
        min_tp = turning_points.get()
        # min_tp.y is a whole number (MIDI pitch) so we can cast it to an int
        i = int(min_tp.y)

        # Each Turning Point changes the SLOPE of the total intersection: a turning point dictates the behaviour of the score up to the next Turning Point. So every time we take out a new turning point from the priority queue, the first thing we have to do is update the score.
        # Update total intersection value
        if min_tp.x != C_h[i].prev_tp.x:
            C_h[i].value += C_h[i].slope * (min_tp.x - C_h[i].prev_tp.x)

        # Keep track of best matches
        if C_h[i].value > best: # New record!
            list_of_shifts = [] # Reset list of accepted translations
            best = C_h[i].value
        # Append a translation if it hasn't been added already
        if C_h[i].value >= best and min_tp not in list_of_shifts:
            list_of_shifts.append(min_tp)

        # Update slope
        if min_tp.type in [0, 3]:
            C_h[i].slope += 1
        else:
            C_h[i].slope += -1

        # Save current turning point so other TP's know long it has been since the value has been updated
        C_h[i].prev_tp = min_tp
        # Find next turning point of this type (move pointer forward)
        if min_tp.source_index < len(source) - 1:
            if min_tp.type == 0 or min_tp.type == 1:
                turning_points.put(TurningPoint(min_tp.pattern_segment, source_onset_sort[min_tp.source_index + 1], min_tp.source_index + 1, min_tp.type))
            else: # type == 2 or 3
                turning_points.put(TurningPoint(min_tp.pattern_segment, source_offset_sort[min_tp.source_index + 1], min_tp.source_index + 1, min_tp.type))

    return list_of_shifts

