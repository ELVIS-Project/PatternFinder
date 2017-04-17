from LineSegment import LineSegmentSet
from Queue import PriorityQueue
import music21
import copy
import pdb

def S2(pattern, source, threshold = 2, scale = 0, window = 10):

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

    return report_Ktable_occurrences(kappa, source_set)
    """
    ### REPORT SHIFTS ###
    list_of_shifts = []
    for r in kappa[1:]: #Ignore kappa's first element so that it indexes from 1
        source_indices = []
        ptr = r
        while ptr['y'] != None:
            source_indices.append(ptr['b'])
            ptr = ptr['y']
        source_indices.append(ptr['a'])

        list_of_shifts.append((ptr['s'], source_set[ptr['a']] - pattern_set[0]))

        # Colour the notes
        for i in source_indices:
            if source_set[i].note != None:
                source_set[i].note.color = 'red'

    if scale == 0:
        return [shift[1] for shift in list_of_shifts]
    else:
        return [shift[1] for shift in list_of_shifts if shift[0] == scale]
    """

def report_Ktable_occurrences(results, source_set):
    occurrences = music21.stream.Stream()
    for r in results[1:]: #results indexes from 1
        result_stream = music21.stream.Stream()
        occurrences.append(result_stream)

        ptr = r
        while ptr != None:
            result_stream.append(source_set[ptr['b']].note)
            if ptr['y'] == None:
                result_stream.append(source_set[ptr['a']].note)
            ptr = ptr['y']

    return occurrences
