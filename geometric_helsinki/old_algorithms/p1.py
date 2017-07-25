from more_itertools import peekable
from pprint import pformat # for logging
from geometric_helsinki.algorithms.base import P
import logging
import NoteSegment
import music21
import pdb

class P1(P):
    """
    INPUT:
        pattern - sorted flattened music21 stream of notes (no chords)
        source - another sorted flattened music21 stream of notes (no chords)
        settings - dictionary
    OUTPUT:
        a list of InterNoteVectors indicating each matching pair within an exact, pure occurrence of the pattern within the source

    Modification from pseudocode code. Skips this line:
        ptrs[p] = max(ptrs[p], p + t)

    POLYPHONIC BEHAVIOUR
        P1 can find exact melodic occurrences through many voices. It will only find multiple matches if the first note of the pattern can match more than one identical note in the source, while all the rest of the notes find possibly non-unique matches. THIS should be changed.


    UKKONEN PSEUDOCODE
        ### (1) for j <- 1, ..., n-m do
        # Any solution to the P1 specification must at least match p_0 with a segment in source. So we loop through all possible matches for p_0, and ascertain whether any of the resulting shifts also induce a total match for the whole pattern. There are n - m + 1 possible matches (the pseudocode in the paper appears to have missed the + 1).
            ### (3) for j <- 1, ..., n - m do
            # Find exact matches for p_1, ..., p_m
    POLYPHONIC BEHAVIOUR:

                ### (8) q_i <- max(q_i, t_j)
                # The first value for q_i is either its offset from the match of p_0 (s_j), or its previous value from the last iteration. We take the maximum because q_i is non-decreasing.
                # p + t will never be greater than len(source).
                # the choice of p + t as a minimum possible match for p_i implies that two unison voices in the pattern cannot match to a single voice in the source. Every note in the pattern must have a unique matching note in the source.
                ### (9) while q_i < p_i + f
                    ### (9) q_i <- next(q_i)

                ### (10) until q_i > p_i + f
                # Check if there is no match for this p_i. If so, there is no exact match for this t_j. Break, and try the next one.
                ### (11) if i = m + 1 then output(f)

    """
    def algorithm(self):
        def is_pure_occurrence(ptrs, cur_shift):
            for inter_vector_gen in ptrs[1:]:
                # Take the first intervec that's too big.
                # If you use itertools.takewhile, it will consume the first one that's
                # too big, # but you want to keep it in the generator for subsequent cur_shifts.
                try:
                    while inter_vector_gen.peek() < cur_shift:
                        inter_vector_gen.next()

                    # TODO add if cndt_intr_vector.peek() == cur_shift, take it.
                    # Then make is_pure_occurrence a generator,
                    # so we can find multiple matches if there are duplicated notes
                    if inter_vector_gen.peek() != cur_shift:
                        return False
                except StopIteration:
                    return False
            # If we've gotten down here, then there are enough matching pairs to
            # constitute a pure, exact match!
            return True

        ptrs = [p.source_ptrs[1] for p in self.patternPointSet]

        # At the very least, p_0 must match, so we use this shift as a candidate
        for cur_shift in ptrs[0]:
            # Then we look at the rest of the pointers to see if they also can form a matching pair with this shift
            self.logger.debug('Checking if cur_shift %s causes a pure occurrence...',
                    cur_shift)
            if is_pure_occurrence(ptrs, cur_shift):
                yield [cur_shift] + [x.peek() for x in ptrs[1:]]
            else:
                self.logger.debug("Not a pure occurrence. Current ptrs: \n %s",
                        pformat([cur_shift] + [x.peek() for x in ptrs[1:]]))

