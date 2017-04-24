from LineSegment import TwoDVector, LineSegment
from Queue import PriorityQueue
import geoAlgorithm
import NoteSegment
import music21
import pdb

class P2(geoAlgorithm.geoAlgorithmP):

    def __init__(self, pattern_score, source_score, settings = geoAlgorithm.DEFAULT_SETTINGS):
        # TODO why don't i have to return this next statement?
        super(P2, self).__init__(pattern_score, source_score, settings)

    def run(self):
        super(P2, self).run()

    def process_results(self, results):
        return super(P2, self).process_results(results)

    def algorithm(self, pattern, source, settings):
        """
        Input: two lists of horizontal line segments. One is the 'pattern', which we are looking for in the larger 'source'
        Output: all horizontal / vertical line segment shifts which shift the pattern so that it shares a subset with the source

        The # of mismatches between source and pattern is defined as len(pattern) - # of matches between pattern and source.
        """
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

        # TODO Temporary fix
        occurrences = music21.stream.Stream()
        result_stream = music21.stream.Stream()

        # Pointers which refer to source INDICES. q_i points to s_i, a potential match for p_i
        q = [0 for s in range(len(pattern))]

        # Fill the priority queue 
        for i in range(len(pattern)):
            # priority queue members are tuples:
            #   1) f_i = s_{q_i} - p_i ;;; the shift which brings ith pattern to the q_ith source 
            #   2) i ;;; the index of this pattern element
            shifts.put([source[q[i]] - pattern[i], i, q[i]])

        while(shift_candidate < TwoDVector(float("inf"), float("inf"))):
            ## min(F)
            min_shift = shifts.get()
            # index of the pattern p_i which corresponds to this minimum shift
            p_i = min_shift[1]
            ## update(F): q_i <- next(q_i), and put the new translation into the pq
            q[p_i] += 1

            if q[p_i] < len(source):
                #Optionally, here we can check for duration match as well
                shifts.put([source[q[p_i]] - pattern[p_i], p_i, q[p_i]])

            ## Keep count
            # TODO couldn't this break if there were two incomplete partial matches of the same shift?
            # TODO lemstrom query A, adds both a's, since they both contribute to the same shift.
            # The shifts are in order, even if they aren't pushed to the queue yet. the min shift, if part of a larger chain in the same shift, will be push a similar min shift, which will get pulled right away!
            if shift_candidate == min_shift[0]:
                #TODO temp fix
                source_note = source[min_shift[2]].note_link
                result_stream.insert(source_note.getOffsetBySite(self.source.flat.notes), source_note)
                c += 1
            else:
                if shift_candidate != TwoDVector(float("-inf"), float("-inf")):
                    # Save shift candidates with their multiplicity
                    shift_matches.append([shift_candidate, c])
                    #TODO temp fix
                    occurrences.append(result_stream)
                shift_candidate = min_shift[0]
                c = 1

                if min_shift[0] != TwoDVector(float("inf"), float("inf")):
                # TODO temp fix
                # last note in source is infinity, so this stops the loop. we don't want to add infinity to the stream.
                    result_stream = music21.stream.Stream()
                    source_note = source[min_shift[2]].note_link
                    result_stream.insert(source_note.getOffsetBySite(self.source.flat.notes), source_note)

        pdb.set_trace()
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
