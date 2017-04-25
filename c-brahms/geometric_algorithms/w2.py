from LineSegment import LineSegmentSet
from Queue import PriorityQueue
from geometric_algorithms import geoAlgorithm
import music21
import copy
import pdb

class W2(geoAlgorithm.SW):

    def process_results(self):
        self.results = self.results[1:]
        if self.settings['threshold'] == 'max':
            max_length = max(self.results, key=lambda x: x.w).w
            self.results = filter(lambda x: x.w == max_length, self.results)
        return super(W2, self).process_results()

    def algorithm(self):
        pattern = self.pattern
        source = self.source
        settings = self.settings
        threshold = settings['threshold']
        if threshold == "exact":
            threshold = len(self.pattern.flat.notes) - 1 # recall the length of an occurrence is in # of vectors, so the max # of vectors is len - 1
        if threshold == "max":
            threshold = 2
        scale = settings['scale']

        pqueues = [PriorityQueue() for table in pattern.K]

        # TODO figure out kappa indexing
        kappa = [None] # list of occurrence chains (really just has the last db intra vector of each chain)

        ### Lemstrom's Pseudocode ###

        ### INITIALIZE QUEUES FROM ALL KTABLES ###
        ## (0) l <-- 0; K[0]_\sum_{p_0}.s <-- infinity
        ## (1) for i <-- 0,...,m-2
            ## (2) for j <-- 0,...,\sum_{p_0} ### Should be "p_i", I reckon a typo in the pseudocode. also why not \sum_{p_i} -1
                ## (3) Q_{K[i]_j}.c^{b,s} <-- push(&K[i]_j) # c should be out of bounds here if it's initialized with len(pattern)?
        l = 0 # number of occurrences
        pattern.K[0][-1].e = float("inf")
        for i in range(len(pattern.flat.notes) - 1): #ignore last K table
            K = pattern.K[i]
            for j in range(len(K)):
                #TODO temporary fix. don't push the last row unless it's the first K table
                if i > 0 and j == (len(K) - 1):
                    continue
                lex_order = (K[j].b, K[j].a)
                pqueues[K[j].c].put((lex_order, K[j]))

        ### LOOP THROUGH ALL K TABLES EXCEPT THE FIRST
        ## (4) for i <-- i,...,m-2 do
            ## (5) q <-- pop(Q_i^{b,s})
            ## (6) for j <-- 0,...,\sum_{p_i} - 1 do
                ## (6.5) if [q.b, q.s] > [K[i]_\sum_{p_i}.a, K[i]_\sum_{p_i}.s] break
                ## (7) while [q.b, q.s] < [K[i]_j.a, K[i]_j.s] do
                    ## (8) q <-- pop(Q_i^{b,s})
        i = 1 # TODO indexing for PQs, clean it up so you don't need this
        for K_table in pattern.K[1:-1]:
            # TODO this will make the program wait() if len(pattern)=0
            q = pqueues[i].get_nowait()[1] # q is an intra db vector which matches some pattern vector that ends at pattern index q['c']. use [1] to ignore lex_order tuple
            for K_row in K_table:
                # I don't understand this line too well:
                if (q.b, q.e) > (K_table[-1].a, K_table[-1].e):
                    break
                while (q.b, q.e) < (K_row.a, K_row.e):
                    q = pqueues[i].get_nowait()[1]

                ### BINDING OF EXTENSION ###
                ## (9) if [q.b, q.s] = [K[i]_j.a, K[i]_j.s] then
                if (q.b, q.e) == (K_row.a, K_row.e):

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
                    r = pqueues[i].get_nowait()[1]
                    while (r.b, r.e) == (q.b, q.e):
                        if r.w >= q.w:
                            q = r
                        r = pqueues[i].get_nowait()[1]
                    # put r back so that pqueues.get() acts more like a 'peek'
                    lex_order = (r.b, r.a)
                    pqueues[i].put((lex_order, r))

                    ## (13) K[i]_j.w <-- q.w + 1
                    ## (14) K[i]_j.y <-- q
                    K_row.w = q.w + 1 # increment the continuous length of this occurrence (continuous relative to the pattern)
                    K_row.y = q # backtracking pointer

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
                    if K_row.w == threshold:
                        l += 1 # increment the number of occurrences found
                        K_row.z = l # link the end of the chain with the occurrence index
                        kappa.append(K_row)

                    ### UPDATING OLD OCCURRENCES ###
                    #
                    ## (19) if K[i]_j.w > \alpha then
                        ## (20) K[i]_j.z = q.z
                        ## (21) \kappa[q.z] = (&K[i]_j)
                    if K_row.w > threshold:
                        K_row.z = q.z
                        # Keep in mind kappa[q.z] must exist. Each occurence will increase the length of its chain incrementally by 1, so lines (15-18) of the pseudocode can never be skipped
                        kappa[q.z] = K_row

                    ### Put the end of this occurence chain back in the priority queue
                    ## (22) Q_{K[i]_j.c}^{b,s} <-- push(&K[i]_j) 
                    lex_order = (K_row.b, K_row.a)
                    pqueues[K_row.c].put((lex_order, K_row))

            ## (23) K[i]_\sum{p_i}.s <-- \infinity
            ## (24) Q_{i+1}^{b,s} <-- push(&K[i]_\sum{p_i})
            K_table[-1].e = float("inf")
            lex_order = (K_table[-1].b, K_table[-1].a)
            pqueues[i+1].put((lex_order, K_table[-1]))
            i += 1 # Indexing for PQs, clean it up so you don't need this

        return kappa
