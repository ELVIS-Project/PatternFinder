from LineSegment import TwoDVector, LineSegment
from Queue import PriorityQueue
import geoAlgorithm
import NoteSegment
import music21
import pdb

class P2(geoAlgorithm.P):

    def pre_process(self):
        super(P2, self).pre_process()
        if self.settings['threshold'] == 'all':
            pass

    def process_results(self):
        if self.settings['threshold'] == "all":
            return self.results
        elif self.settings['threshold'] == "max":
            # Default: minimize the mismatches
            temp_threshold = len(max(self.results, key=lambda x: len(x)))
        else:
            # Return shifts with more than or equal to settings['threshold'] matches
            temp_threshold = int(self.settings['threshold'])
        for r in self.results:
            if len(r) < temp_threshold:
                self.results.remove(r)

        return super(P2, self).process_results()


    def algorithm(self):
        """
        Input: two lists of horizontal line segments. One is the 'pattern', which we are looking for in the larger 'source'
        Output: all horizontal / vertical line segment shifts which shift the pattern so that it shares a subset with the source

        The # of mismatches between source and pattern is defined as len(pattern) - # of matches between pattern and source.
        """
        # TODO test this with a case where the source has half of the pattern query, but repeated at the same time in two parts. i think it'll think it's a perfect match.
        pattern = self.pattern_line_segments
        source = self.source_line_segments
        settings = self.settings

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
                # TODO sometimes the note is already in the result stream. that must mean that a previous shift, in the same class of candidate, originated from this note, and pointed to a different? but same unison source note. so if it's already there.. continue?
                try:
                    result_stream.insert(source_note.getOffsetBySite(self.source.flat.notes), source_note)
                except music21.stream.StreamException as e:
                    continue
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

        """
        # Return all possible shifts and their multiplicities
        if settings['threshold'] == "all" or settings['threshold'] == 'max':
            return shift_matches
        else:
            # Return shifts only with 'settings['threshold']' number of mismatches
            try:
                settings['threshold'] = int(settings['threshold'])
            # Default: minimize the mismatches
            except TypeError:
                settings['threshold'] = len(pattern) - max(zip(*shift_matches)[1])
        """

        # Return shifts with the given mismatch
        # number of mismatches is relative to the length of the pattern (not the length of the source).
        #return [shift[0] for shift in shift_matches if shift[1] == len(pattern) - settings['threshold']]
        return occurrences
