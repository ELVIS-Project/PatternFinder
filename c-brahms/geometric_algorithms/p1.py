from LineSegment import LineSegment
from itertools import takewhile
from more_itertools import peekable
from NoteSegment import InterNoteVector
from geometric_algorithms.geo_algorithms import P
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

    POLYPHONIC BEHAVIOUR:
        P1 can find exact melodic occurrences through many voices. It will only find multiple matches if the first note of the pattern can match more than one identical note in the source, while all the rest of the notes find possibly non-unique matches. THIS should be changed.
    """
    def filter_result(self, result):
        return True

    def algorithm(self):
        def is_pure_occurrence(ptrs):
            for inter_vector_gen in ptrs[1:]:
                # Take the first intervec that's too big. if you use itertools.takewhile, it will consume the first one that's too big, but you want to keep it in the generator for subsequent cur_shifts.
                try:
                    while inter_vector_gen.peek() < cur_shift: inter_vector_gen.next()

                    # TODO add if cndt_intr_vector.peek() == cur_shift, take it. Then make is_pure_occurrence a generator, so we can find multiple matches if there are duplicated notes
                    if inter_vector_gen.peek() != cur_shift:
                        return False
                except StopIteration:
                    return False
            # If we've gotten down here, then there are enough matching pairs to constitute a pure, exact match!
            return True

        source = self.sourcePointSet
        pattern = self.patternPointSet

        ptrs = [peekable((lambda p: (InterNoteVector(p, pattern, s, source) for s in source))(note)) for note in pattern]

        # At the very least, p_0 must match, so we use this shift as a candidate
        for cur_shift in ptrs[0]:
            # Then we look at the rest of the pointers to see if they also can form a matching pair with this shift
            if is_pure_occurrence(ptrs):
                yield [cur_shift] + map(lambda x: x.peek(), ptrs[1:])



    def algorithmOld(self):
        """
        POLYPHONIC BEHAVIOUR:
            P1 can find exact melodic occurrences through many voices. It will only find multiple matches if the first note of the pattern can match more than one identical note in the source, while all the rest of the notes find possibly non-unique matches. THIS should be changed.
        """
        self.pattern_line_segments = [LineSegment(note.getOffsetBySite(self.pattern.flat.notes), note.pitch.ps, note.duration.quarterLength, note_link=note) for note in self.pattern.flat.notes]
        self.source_line_segments = [LineSegment(note.getOffsetBySite(self.source.flat.notes), note.pitch.ps, note.duration.quarterLength, note_link=note) for note in self.source.flat.notes]
        source = self.source_line_segments
        pattern = self.pattern_line_segments
        settings = self.settings
        #TODO put this comment in a higher level file: triple-pound comments (###) reference Ukkonen's pseudocode.

        # Lexicographically sort the pattern and source
        pattern.sort()
        source.sort()

        # Store Results
        shift_matches = []

        # A list of pointers referred to as "q_i". There is one for each pattern line segment p_i. q_i pointers refer to a possible match between p_i and a segment in the source called s_j.
        ptrs = [0 for p in pattern]

        ## TODO this is a temp fix
        occurrences = music21.stream.Stream()

        ### (1) for j <- 1, ..., n-m do
        # Any solution to the P1 specification must at least match p_0 with a segment in source. So we loop through all possible matches for p_0, and ascertain whether any of the resulting shifts also induce a total match for the whole pattern. There are n - m + 1 possible matches (the pseudocode in the paper appears to have missed the + 1).
        for t in range(len(source) - len(pattern) + 1):

            ## TODO this is a temp fix
            possible_occ = music21.stream.Stream()
            possible_occ.insert(source[t].note_link.getOffsetBySite(self.source.flat.notes), source[t].note_link)
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
                if settings['segment'] == True:
                    if source[ptrs[p]] != pattern[p] + shift or source[ptrs[p]].duration != pattern[p].duration: break
                else: # or if option == 'onset':
                    if source[ptrs[p]] != pattern[p] + shift: break

                ### (11) if i = m + 1 then output(f)
                # Check if we have successfully matched all notes in the pattern

                ## TODO this is a temp fix
                source_note = source[ptrs[p]].note_link
                possible_occ.insert(source_note.getOffsetBySite(self.source.flat.notes), source_note)

                if p == len(pattern)-1:
                    shift_matches.append(shift)
                    occurrences.append(possible_occ)

        return occurrences
