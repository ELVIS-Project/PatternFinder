from Queue import PriorityQueue
from geometric_algorithms import geo_algorithms
import music21
import copy
import pdb

class S2(geo_algorithms.S):

    def algorithmAlsoOld(self):
        """
        Algorithm S2 returns "time-scaled" and "partial" occurrences of the pattern
        within the source.

        Filters:
            'scale' : Only accepts occurrences of a particular scale
            'source_window' : Limits the search space by limiting the number
                of intervening notes allowed between any two source notes
                within the occurrence
                e.g. we do not want to match the first and last notes of the
                    source and call that a sensible occurrence. Also, that would
                    require an enormous search space depending on the score.
            'pattern_window' : Similar to 'source_window' but applies to the
                number of missing notes between any two matched pattern notes.

        Runtime
        It's shown in Lemstrom's paper that the runtime works out to:
            O(m * n * pattern_window * source_window * log(n))

        Summary of Implementation: precompute all of the possible IntraNoteVectors
        in both the pattern and source. Then try to match them and form chains.

        Linesweep through the pattern. Remember that the final pattern note
        does not have a K table since K tables correspond to intra_vectors
        starting at a particular pattern note (and vectors starting at
        the last pattern note have nowhere to go!)

        Similarly, since at each iteration we are trying to extend chains
        stored in PQ's referencing antecedent K_tables, we start with the
        second table since that's the first one with an associated PQ

        Don't push a K_table entry to a later PQ if it didn't extend a chain.
        Remember that you already initialized all the PQ's and K table entries
        with length-one chains! Here we are looking for longer ones.

        The PQ's represent all of the current chains which END at the corresponding
        pattern note. That's why we push new extensions to K_entry.noteEnd.PQ

        Since ALL of the queues are initialized in pre_process, rather than
        just the first one (as in the pseudocode of S1), I think this algorithm
        will be able to find suffixes of perfect matches. But that's ok because
        we'll end up using Antti Laaksonen's faster version anyways.

        Since we yield every extension, the chain can be outputted as it is built.
        e.g. with a pattern of size 5 and a threshold of 4, we'll return all of the
        length-4 subsequences of the perfect match as well. (I think..)
        """
        for p in self.patternPointSet[1:-1]:
            for K_row in p.K_table:
                antecedent = lambda: (p.PQ.queue[0].item.sourceVec.noteEndIndex, p.PQ.queue[0].item.scale)
                binding = (K_row.sourceVec.noteStartIndex, K_row.scale)

                # Use peek so that the first intra_vec to break this K_row can still be used for the next one
                while (p.PQ.qsize() > 0) and (antecedent() < binding):
                    p.PQ.next()

                # Modification to pseudocode: use "while" instead of "if" so that
                # you can chain many possible identical notes
                while (p.PQ.qsize() > 0) and (antecedent() == binding):
                    q = p.PQ.next()
                    new_entry = K_entry(K_row.patternVec, K_row.sourceVec, w = q.w + 1, y = q)
                    new_entry.patternVec.noteEnd.PQ.put(new_entry)
                    yield new_entry


    def algorithmOld(self):
        ## TODO pass this stuff in, or rename in code?
        pattern = self.pattern
        source = self.source
        settings = self.settings
        threshold = settings['threshold']

        ## TODO put this in a pre_process function along with initializing Ktables 'n stuff
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
        pattern.K[0][-1].s = float("inf")
        for i in range(len(pattern.flat.notes) - 1): #ignore last K table
            K = pattern.K[i]
            for j in range(len(K)):
                #TODO temporary fix. don't push the last row unless it's the first K table
                if i > 0 and j == (len(K) - 1):
                    continue
                lex_order = (K[j].b, K[j].s)
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
                if (q.b, q.s) > (K_table[-1].a, K_table[-1].s):
                    break
                while (q.b, q.s) < (K_row.a, K_row.s):
                    q = pqueues[i].get_nowait()[1]

                ### BINDING OF EXTENSION ###
                ## (9) if [q.b, q.s] = [K[i]_j.a, K[i]_j.s] then
                if (q.b, q.s) == (K_row.a, K_row.s):

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
                    while (r.b, r.s) == (q.b, q.s):
                        if r.w > q.w: #TODO check pseudocode for >= or >
                            q = r
                        r = pqueues[i].get_nowait()[1]
                    # put r back so that pqueues.get() acts more like a 'peek'
                    lex_order = (r.b, r.s)
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
                    lex_order = (K_row.b, K_row.s)
                    pqueues[K_row.c].put((lex_order, K_row))

            ## (23) K[i]_\sum{p_i}.s <-- \infinity
            ## (24) Q_{i+1}^{b,s} <-- push(&K[i]_\sum{p_i})
            K_table[-1].s = float("inf")
            lex_order = (K_table[-1].b, K_table[-1].s)
            pqueues[i+1].put((lex_order, K_table[-1]))
            i += 1 # Indexing for PQs, clean it up so you don't need this

        return kappa
