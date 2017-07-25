from geometric_algorithms import geoAlgorithm
from NoteSegment import NoteVector
from collections import namedtuple
import music21
import pdb

class DPW2(geoAlgorithm.SW):


    def process_results(self):
        pass
        """
        self.results = self.results[1:]
        if self.settings['threshold'] == 'max':
            max_length = max(self.results, key=lambda x: x.w).w
            self.results = filter(lambda x: x.w == max_length, self.results)
        return super(DPW2, self).process_results()
        """

    def algorithm(self):
        def fill_M(M, cur_p, cur_s, last_p, last_s):
            """
            cur_p index of current  pattern note
            cur_s index of current source note
            last_p number of indices from current p note till last p we took
            last_s number of indices from current s note till last s we took

            ex: index of the last p we took is cur_p - last_p
            """
            if M[cur_p][cur_s][last_p][last_s] != -1:
                return M[cur_p][cur_s][last_p][last_s]

            # Base case
            if cur_s >= len(source) or cur_p >= len(pattern):
                return 0

            chain = namedtuple("chain", ['best', 'next_ind'])
            best = 0

            # Option 1: Increase chain with cur_s, cur_p as a match
            intra_database_vector = NoteVector(source[cur_s - last_s], source[cur_s], source)
            intra_pattern_vector = NoteVector(pattern[cur_p - last_p], pattern[cur_p], pattern)
            if intra_database_vector.y == intra_pattern_vector.y:
                a = fill_M(M, cur_p + 1, cur_s + 1, 1, 1)
                best = max(a + 1, best)

            # Option 2: Try next source note
            if last_s < settings['window']:
                a = fill_M(M, cur_p, cur_s + 1, last_p, last_s + 1)
                best = max(a, best)

            # Option 3: Try next pattern note (Partial matching DPW2 only)
            a = fill_M(M, cur_p + 1, cur_s, last_p + 1, last_s)
            best = max(a, best)

            M[cur_p][cur_s][last_p][last_s] = best
            return best

        pattern = self.pattern.flat.notes
        source = self.source.flat.notes
        settings = self.settings

        M = [[[[-1 for p in range(len(source) + 1)] for s in range(len(pattern) + 1)] for p in range(len(source) + 1)] for s in range(len(pattern) + 1)]

        for i in range(len(pattern)):
            for j in range(len(source)):
                fill_M(M, i + 1, j + 1, 1, 1)

        #TODO pcur, last_p.. these are vectors! and isn't there a way to use iterators instead of +1 indexing?


        return M
