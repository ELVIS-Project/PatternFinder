from geometric_algorithms import geo_algorithms
from NoteSegment import InterNoteVector, K_entry # to create occurrence chains
from LineSegment import LineSegmentSet
from pprint import pprint, pformat
from itertools import groupby
import copy
import pdb


class S1(geo_algorithms.S):

    def pre_process(self):
        super(S1, self).pre_process()
        self.settings['threshold'] = len(self.patternPointSet)
        self.settings['pattern_window'] = 1

    def algorithmAlsoOld(self):

        for p in self.patternPointSet[1:-1]:
            for K_row in p.K_table:
                antecedent = lambda: p.PQ.queue[0].item.noteEndIndex
                binding = K_row.noteStartIndex

                # Use peek so that the first intra_vec to break this K_row can still be used for the next one
                while (p.PQ.qsize() > 0) and (antecedent() < binding):
                    p.PQ.next()

                # Modification to pseudocode: use "while" instead of "if" so that
                # you can chain many possible identical notes
                while (p.PQ.qsize() > 0) and (antecedent() == binding):
                    q = p.PQ.next()
                    new_entry = K_entry(K_row.patternVec, K_row, w = q.w + 1, y = q)
                    new_entry.patternVec.noteEnd.PQ.put(new_entry)
                    yield new_entry
    def algorithmOld(self):
        """
        Input: Two NoteSegments streams: one called the pattern, which we are looking for occurrences within the larger source.
        Output: all shifts which result in a time-scaled occurrence of the pattern

        Assumes that:
        1) both the source and pattern are sorted lexicographically by (onset, pitch)

        Settings which alter the behaviour of the algorithm:
        window defaults to 10 ; an unlimited window will square the runtime

        Settings which filter the results:
        scale = "all" ; by default, the algorithm does not filter any results

        TODO: Ktable initialization should happen outside the algorithm so that it isn't done twice for S1 and S2. But then you'd need a wrapper function so that you can still call S1 on music streams.
        """
        # notes
        ## (n) Lemstrom's pseudocode
        ### large structural things ###

        #TODO remove these, change the names in the code
        pattern = self.pattern
        source = self.source
        settings = self.settings

        """
##
        print("INITIALIZED K TABLES \n")
        pprint(pattern.K)
##
        """

        # A list of priority queues which refer to table K[i-1]
        # TODO calculate max size of each PriorityQueue and put it in the arg?
        ## TODO subclass priority queue
        # 1) so you can have a keyfunc rather than inputting tuples all the time. then you wouldn't need specify [1] after .get()
        # 2) to implement a peek() function
        pqueues = [PriorityQueue() for table in pattern.K]

        ### INITIALIZE FIRST PRIORITY QUEUE WITH THE FIRST K TABLE ###
        ## (0) K[0]_\sum{p_0}.s <-- \infinity
        ## (1) for j <-- 0,...,\sum_{p_0} do
            ## (2) Q_1^{b,s} <-- push(&K[0]_j) "whose entires are addressed to K_rows..."
        pattern.K[0][-1].s = float("inf")
        for K_row in pattern.K[0]:
            lex_order = (K_row.b, K_row.s) # PQs are sorted lexicographically by (b, s)
            pqueues[1].put((lex_order, K_row)) # PQ[i] refers to K_{i-1}

        """
##
        print("INITIALIZED QUEUES \n")
        pprint(pqueues)
##
        """

        ### LOOP THROUGH ALL THE REMAINING K TABLES ###
        #TODO why not all the way to len(pattern)? why skip the last K table? (skip or the algy doesn't work)
        #####
        ## (3) for i <-- 1,..., m - 2 do
            ## (4) q <-- pop(Q_i^{b,s})
            ## (5) for j <-- 0,...,\sum_{p_i} - 1 do
        i = 1 # TODO not sure if indexing is necessary
        for K_table in pattern.K[1:-1]:
            q = pqueues[i].get_nowait()[1] #[1]-- get the :dict: and ignore the lex order tuple
            for K_row in K_table[:-1]: # TODO this deviates from pseudocode and skips the last K_row of the K table. why?
                ### FIND AN ANTECEDENT OF THE BINDING 
                ## (6) while [q.b, q.s] < [K[i]_j.a, K[i]_j.s] do
                    ## (7) q <-- pop(Q_i^{b,s}
                while (q.b, q.s) < (K_row.a, K_row.s):
                    q = pqueues[i].get_nowait()[1]

                ### BINDING OF EXTENSION
                ## (8) if [q.b, q.s] = [K[i]_j.a, K[i]_j.s] then
                    ## (9) K[i]_j.w <-- q.w + 1 update length
                    ## (10) K[i]_j.y <-- q store backtracking link
                    ## (11) Q_{i+1}^{b,s} <-- push(&K[i]_j)
                    ## (12) q <-- pop(Q_i^{b,s})
                if (q.b, q.s) == (K_row.a, K_row.s):
                    K_row.w = q.w + 1
                    K_row.y = q # backlink: K_row.y will point to the same K entry as q does
                    lex_order = (K_row.b, K_row.s)
                    #new_K_row = copy.deepcopy(K_row) #TODO copy necessary?
                    pqueues[i+1].put((lex_order, K_row))
                    q = pqueues[i].get_nowait()[1]

            ## (13) K[i]_\sum_{p_i}.s <-- \infinity
            ## (14) Q_{i+1}^{b,s} <-- push(&K[i]_\sum_{p_i})
            K_table[-1].s = float("inf")
            #new_K_row = copy.deepcopy(K_table[-1]) # #TODO copy necessary?
            lex_order = (K_table[-1].b, K_table[-1].s)
            pqueues[i+1].put((lex_order, K_table[-1]))
            i += 1 #TODO not sure indexing is necessary

        ### REPORT OCCURRENCES
        results = [K_row for K_row in pattern.K[-2] if K_row.w == (len(pattern.flat.notes) - 1)]
        return results
