from Queue import PriorityQueue # Lemstrom's choice of data structure
from LineSegment import LineSegmentSet
import copy


def S1(pattern, source, **settings):
    """
    Input: two lists of horizontal line segments. One is the 'pattern', which we are looking for in the larger 'source'
    Output: all shifts which result in a time-scaled occurrence of the pattern
    """
    # notes
    ## (n) Lemstrom's pseudocode
    ### large structural things ###


    ### Settings which alter the behaviour of the algorithm
    window = 10 # an unlimited window will square the runtime
    if settings.has_key['window']:
        window = setings['window']

    ### Settings which filter the results
    scale = "all" # by default, do not filter any results
    if settings.has_key('scale'):
        scale = settings['scale']


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







