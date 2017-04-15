"""
Algorithms P1, P2 and P3 are described in the following publication:

Ukkonen, Esko; Lemstrom, Kjell; Makinen, Veli:
Geometric algorithms for transposition invariant content-based music retrieval.
in Proc. 4th International Conference on Music Information Retrieval, pp. 193-199, 2003.
https://tuhat.halvi.helsinki.fi/portal/services/downloadRegister/14287445/03ISMIR_ULM.pdf

In addition to Ukkonen's paper, we follow a ruby implementation by Mika Turkia, found at https://github.com/turkia/geometric-mir-algorithms/blob/master/lib/mir.rb
"""

from LineSegment import LineSegment, LineSegmentSet, TurningPoint, TwoDVector, Bucket
from Queue import PriorityQueue # Lemstrom's choice of data structure
import itertools
import midiparser
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
    shifts = PriorityQueue(len(pattern) * len(source))
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
    turning_points = PriorityQueue(4 * len(pattern))
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

def S1(pattern, source, window = 0, scale = 0, start = 0):
    # TODO wrap window, start into an **option unpacked dict
    """
    Input: two lists of horizontal line segments. One is the 'pattern', which we are looking for in the larger 'source'
    Output: all shifts which result in a time-scaled occurrence of the pattern
    """
    # notes
    ## (n) Lemstrom's pseudocode
    ### large structural things ###

    # window == 0 --> no windowing
    if window == 0:
        window = len(source)

    # TODO where exactly do these need to be sorted? in initKtables? in compute_vectors? Here? when we init the segment Set?
    source_set = LineSegmentSet(sorted(source))
    pattern_set = LineSegmentSet(sorted(pattern))

    #Result
    results = []

    # TODO sort K tables in order (a, b, s)?
    pattern_set.initialize_Ktables(source_set, source_window = window)

    # A list of priority queues which refer to table K[i-1]
    # TODO calculate max size of each PriorityQueue and put it in the arg?
    # TODO let the len() depend on size of pattern, since .K depends on size of pattern
    # TODO subclass priority queue so you can have a keyfunc
    pqueues = [PriorityQueue() for table in pattern_set.K]

    # TODO lex_order = lambda x, y, z: (x['y'], x['z'])

    # TODO make a subclass PriorityQueue which implements .get()[1]

    ### INITIALIZE FIRST PRIORITY QUEUE WITH THE FIRST K TABLE ###
    ## (0) K[0]_\sum{p_0}.s <-- \infinity
    pattern_set.K[0][-1]['s'] = float("inf")
    ## (1) for j <-- 0,...,\sum_{p_0} do
    for j in range(len(pattern_set.K[0])):
        ## (2) Q_1^{b,s} <-- push(&K[0]_j) "whose entires are addressed to rows..."
        lex_order = (pattern_set.K[0][j]['b'], pattern_set.K[0][j]['s'])
        # Priority Queue elements look like: ((lex order tuple), :dict: row of K table)
        #TODO clean up how you'll do copy the vector translations
        ktable_dict = copy.deepcopy(pattern_set.K[0][j])
        pqueues[1].put((lex_order, ktable_dict)) # Priority Queue i refers to K_{i-1}

    ### LOOP THROUGH ALL THE REMAINING K TABLES ###
    ## (3) for i <-- 1,..., m - 2 do
    #TODO why not all the way to len(pattern_set)? why skip the last K table?
    for i in range(1, len(pattern_set) - 1): #TODO what if len(pattern_set) < 2?
        K = pattern_set.K[i]
        ## (4) q <-- pop(Q_i^{b,s})
        q = pqueues[i].get()[1] #[1]-- get the :dict: and ignore the lex order tuple

        ## (5) for j <-- 0,...,\sum_{p_i} - 1 do
        for j in range(len(K) - 1):
            ### FIND AN ANTECEDENT OF THE BINDING 
            ## (6) while [q.b, q.s] < [K[i]_j.a, K[i]_j.s] do
            while (q['b'], q['s']) < (K[j]['a'], K[j]['s']):
                ## (7) q <-- pop(Q_i^{b,s}
                q = pqueues[i].get()[1]

            ### BINDING OF EXTENSION
            ## (8) if [q.b, q.s] = [K[i]_j.a, K[i]_j.s] then
            if (q['b'], q['s']) == (K[j]['a'], K[j]['s']):
                ## (9) K[i]_j.w <-- q.w + 1 update length
                K[j]['w'] = q['w'] + 1
                ## (10) K[i]_j.y <-- q store backtracking link
                K[j]['y'] = q # ['y'] will point to the same dictionary as q
                ## (11) Q_{i+1}^{b,s} <-- push(&K[i]_j)
                #TODO clean up how you'll do copy the vector translations
                ktable_dict = copy.deepcopy(K[j])
                pqueues[i+1].put(((K[j]['b'], K[j]['s']), ktable_dict)) # (lex_order, K[j])
                ## (12) q <-- pop(Q_i^{b,s})
                q = pqueues[i].get()[1]

        ## (13) K[i]_\sum_{p_i}.s <-- \infinity
        K[-1]['s'] = float("inf")
        #TODO clean up how you'll do copy the vector translations
        ktable_dict = copy.deepcopy(K[-1])
        ## (14) Q_{i+1}^{b,s} <-- push(&K[i]_\sum_{p_i})
        pqueues[i+1].put(((K[-1]['b'], K[-1]['s']), K[-1]))

    ## (15) if K[m-2]_j.w = m-1 for some 0 <= j <= \sum_{p_{m-2}}
    for j in range(len(pattern_set.K[-2])):
        # Recall that 'w' counts chains of vectors, so for m segments, there must be m-1 vectors in the chain
        if pattern_set.K[-2][j]['w'] == (len(pattern_set) - 1):
           ## (16) Report an occurrence
           results.append(pattern_set.K[-2][j])

    ### REPORT SHIFTS
    list_of_shifts = []
    for r in results:
        ptr = r
        while ptr['y'] != None:
            ptr = ptr['y']
        list_of_shifts.append((ptr['s'], source_set[ptr['a']] - pattern_set[0]))
    if scale == 0:
        return [shift[1] for shift in list_of_shifts]
    else:
        return [shift[1] for shift in list_of_shifts if shift[0] == scale]

def S2(pattern, source, threshold = 2, scale = 0, window = 0):

    # threshold = 0 --> maximal occurrence
    if threshold == 0:
        threshold = len(pattern) - 1 # recall occurrences are measured in number of intra vector matchings, so the max number of these is the length of notes minus one

    ### Copied from S1 ###
    # window == 0 --> no windowing
    if window == 0:
        window = len(source)

    source_set = LineSegmentSet(sorted(source))
    pattern_set = LineSegmentSet(sorted(pattern))
    pattern_set.initialize_Ktables(source_set, source_window = window, pattern_window = len(pattern))

    results = []

    pqueues = [PriorityQueue() for table in pattern_set.K]

    ### Lemstrom's Pseudocode ###
    ## (0) l <-- 0; K[0]_\sum_{p_0}.s <-- infinity
    l = 0 # number of occurrences
    kappa = [None] # list of occurrence chains (really just has the last db intra vector of each chain)
    pattern_set.K[0][-1]['s'] = float("inf")


    ### INITIALIZE QUEUES FROM ALL KTABLES ###
    ## (1) for i <-- 0,...,m-2
    for i in range(len(pattern_set) - 1):
        K = pattern_set.K[i]
        ## (2) for j <-- 0,...,\sum_{p_0} ### Should be "p_i", i reckon a typo in the pseudocode.
        for j in range(len(K)):

            #TODO temporary fix. don't push the last row unless it's the first K table
            if i > 0 and j == (len(K) - 1):
                continue

            ## (3) Q_{K[i]_j}.c^{b,s} <-- push(&K[i]_j)
            ktable_dict = copy.deepcopy(K[j]) # TODO do we need to copy? also future dave, keep in mind that we primarily use the queues for reference
            lex_order = (ktable_dict['b'], ktable_dict['s'])
            pqueues[K[j]['c']].put((lex_order, ktable_dict))

    ### LOOP THROUGH ALL K TABLES EXCEPT THE FIRST
    ## (4) for i <-- i,...,m-2 do
    for i in range(1, len(pattern_set) - 1):
        K = pattern_set.K[i]
        ## (5) q <-- pop(Q_i^{b,s})
        q = pqueues[i].get()[1] # q is an intra db vector which matches some pattern vector that ends at pattern index q['c']. use [1] to ignore lex_order tuple
        ## (6) for j <-- 0,...,\sum_{p_i} - 1 do
        for j in range(len(K)):
            ## (6.5) if [q.b, q.s] > [K[i]_\sum_{p_i}.a, K[i]_\sum_{p_i}.s] break
            if [q['b'], q['s']] > [K[-1]['a'], K[-1]['s']]: # I don't understand this line too well
                break
            ## (7) while [q.b, q.s] < [K[i]_j.a, K[i]_j.s] do
            while [q['b'], q['s']] < [K[j]['a'], K[j]['s']]:
                ## (8) q <-- pop(Q_i^{b,s})
                q = pqueues[i].get()[1]

            ### BINDING OF EXTENSION ###
            ## (9) if [q.b, q.s] = [K[i]_j.a, K[i]_j.s] then
            if [q['b'], q['s']] == [K[j]['a'], K[j]['s']]:

                ### EXTEND THE LONGEST PREFIX OCCURRENCE ###
                # So essentially, of all the intra-db vectors which match
                # an intra pattern vector ending at index 'i', choose the db
                # intra vector which has the longest chain and extend it.
                #
                # Make sure the min() priority queue "peek" doesn't actually
                # modify the priority queue.
                # #TODO I'm pretty sure this means that the length of any occurrence is automatically maximized, unlike P2 which found ALL partial occurrences.
                #####
                ## (10) while min(Q_i^{b,s}) = [q.b, q.s] do
                    ## (11) r <-- pop(Q_i^{b,s})
                    ## (12) if r.w > q.w then q <--r

                ##TODO couldn't you just modify "lex_order" to include 'w' as a third parameter??
                r = pqueues[i].get()[1]
                while [r['b'], r['s']] == [q['b'], q['s']]:
                    if r['w'] > q['w']:
                        q = r
                    r = pqueues[i].get()[1]
                # put r back so that pqueues.get() acts more like a 'peek'
                lex_order = (r['b'], r['s'])
                pqueues[i].put((lex_order, r))

                ## (13) K[i]_j.w <-- q.w + 1
                ## (14) K[i]_j.y <-- q
                K[j]['w'] = q['w'] + 1 # increment the continuous length of this occurrence (continuous relative to the pattern)
                K[j]['y'] = q # backtracking pointer

                ### SAVING NEW OCCURRENCES ###
                # \alpha refers to the threshold: the minimum number
                # of matching pairs (between db intra vectors and 
                # pattern intra vectors) for the set of matching pairs
                # to be considered an "occurrence" (or in the case of S2, 
                # a partial occurrence)
                #
                ## (15) if K[i]_j.w = \alpha then
                    ## (16) l <-- l + 1
                    ## (17) K[i]_j.z = l
                    ## (18) \kappa[l] <-- &K[i]_j
                if K[j]['w'] == threshold:
                    l += 1 # increment the number of occurrences found
                    K[j]['z'] = l # link the end of the chain with the occurrence index
                    kappa.append(K[j])

                ### UPDATING OLD OCCURRENCES ###
                #
                ## (19) if K[i]_j.w > \alpha then
                    ## (20) K[i]_j.z = q.z
                    ## (21) \kappa[q.z] = (&K[i]_j)
                if K[j]['w'] > threshold:
                    K[j]['z'] = q['z']
                    # Keep in mind kappa[q.z] must exist. Each occurence will increase the length of its chain incrementally by 1, so lines (15-18) of the pseudocode can never be skipped
                    kappa[q['z']] = K[j]

                ### Put the end of this occurence chain back in the priority queue
                ## (22) Q_{K[i]_j.c}^{b,s} <-- push(&K[i]_j) 
                ktable_dict = copy.deepcopy(K[j])
                lex_order = (ktable_dict['b'], ktable_dict['s'])
                pqueues[ktable_dict['c']].put((lex_order, ktable_dict))

        ## (23) K[i]_\sum{p_i}.s <-- \infinity
        K[-1]['s'] = float("inf")
        ## (24) Q_{i+1}^{b,s} <-- push(&K[i]_\sum{p_i})
        ktable_dict = copy.deepcopy(K[-1])
        lex_order = (ktable_dict['b'], ktable_dict['s'])
        pqueues[i+1].put((lex_order, ktable_dict))

    ### REPORT SHIFTS ###
    list_of_shifts = []
    for r in kappa[1:]: #Ignore kappa's first element so that it indexes from 1
        ptr = r
        while ptr['y'] != None:
            ptr = ptr['y']
        list_of_shifts.append((ptr['s'], source_set[ptr['a']] - pattern_set[0]))
    if scale == 0:
        return [shift[1] for shift in list_of_shifts]
    else:
        return [shift[1] for shift in list_of_shifts if shift[0] == scale]
