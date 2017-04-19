from itertools import groupby # for use in initializing K tables
from fractions import Fraction
from collections import namedtuple
from pprint import pformat #for K_enry __repr__
import numpy as np
import pandas as pd
import music21
import pdb


#K_entry = namedtuple('K_entry', ['a', 'b', 'y', 'c', 's', 'w', 'z', 'source_vector', 'pattern_vector'])
class K_entry():
    def __init__(self, a, b, y, c, s, w, z, sv, pv):
        self.a = a
        self.b = b
        self.y = y
        self.c = c
        self.s = s
        self.w = w
        self.z = z
        self.source_vector = sv
        self.pattern_vector = pv

    def __repr__(self):
        return pformat(self.__dict__)

class NoteVector():
    #TODO make this a subclass of music21.Music21Object? or maybe even music21.interval.chromaticInterval, with duration != 0?
    """
    A vector from note 'carl' to note 'ralph'. The two note references should be in the same stream 'site'.

    N.T.S: I don't think these NoteVectors ever undergo addition or subtraction, only comparison
    """
    def __init__(self, carl, ralph, site):
        self.start = carl
        self.end = ralph
        self.site = site
        self.x = ralph.getOffsetBySite(site) - carl.getOffsetBySite(site)
        # TODO The papers use base-12 semitones, but I think base 40 would work around this for more precise music retrieval.
        self.y = music21.interval.notesToChromatic(carl, ralph).semitones

    def __cmp__(self, other_vector):
        """
        A lexicographic comparison function. For example, [1,42] < [2,3] and [2,1] < [3,22]
        """
        if (self.x, self.y) < (other_vector.x, other_vector.y):
            return -1
        elif (self.x, self.y) > (other_vector.x, other_vector.y):
            return 1
        return 0

    ##
    # This would work, but you'd need to use __eq__ and others to.
    #def __cmp__(self, other_vector):
        #return (self.x, self.y).__cmp__((other_vector.x, other_vector.y))

    def __repr__(self):
        return "NoteVector({0}, {1}, #{2}: {3} -> #{4}: {5})".format(str(self.x), str(self.y), self.site.index(self.start), self.start, self.site.index(self.end), self.end)


class NoteSegments(music21.stream.Stream):
    # TODO make this a top level stream with a pattern and a source sub stream. would make so much more sense..
    """
    A container for references to the horizontal line segments in a parsed score. Since it's a subclass and is initialized with the score, it still contains all the musical context and metadata of the line segments.
    """
    ###
    # TODO Can't get __init__ function working. After
    #def __init__(self, givenElements = None, *args, **kwargs):
    #    super(NoteSegments, self).__init__(self, givenElements, *args, **kwargs)
    # "givenElements is self" evaluates to true, which is so weird

    def lexicographic_sort(self):
        """
        Helper class to sort the note segments lexicographically by (onset, pitch).
        Uses the priority attribute of music21.Music21Object, which automatically sorts the encompassing stream each time it is changed.
        """
        for n in self.flat.notes:
            n.priority = int(n.pitch.ps) # priority values must be integers, and pitch.ps returns a float. This may lead to some buggy issues with quartertones, since two notes a quarter-tone a part will be treated as identical due to truncation.

    def initialize_Ktables(self, source):
        """
        K-table data structure used in algorithms S1-2, W1-2
        'self' should be a pattern that is to be searched for in asource

        Requires that self, source intra_vectors have already been initialized with their desired windowing
        """
        # Dict comprehension using groupby in order to easily access database vectors based on their pitch translations (y values)
        intra_database_vectors = {key : list(g) for key, g in groupby(source.ivs, lambda x: x.y)}
        # intra_vectors = {key : list(g) for key, g in groupby(self.ivs, lambda x: x.start}

        # There is one K table per note in the pattern
        # TODO make the K table a class so you can have a PQ in it; this will make the algorithm code cleaner (no need to index PQ's)
        self.K = [[] for note in self.flat.notes]

        for f in self.ivs:
            if not intra_database_vectors.has_key(f.y):
                continue
            for g in intra_database_vectors[f.y]:
                # Scale
                if f.x == 0 and g.x == 0:
                    scale = 1
                elif (f.x == float("inf") and g.x == float("inf")) or f.x == 0 or g.x == 0:
                    continue
                else:
                    # Fraction(num, denom) only accepts integers as arguments, so you need to convert g.x and f.x first
                    scale = Fraction(Fraction(g.x), Fraction(f.x))

                # K_entry data
                a = source.flat.notes.index(g.start)
                b = source.flat.notes.index(g.end)
                y = None # backlink for building occurrences
                c = self.flat.notes.index(f.end) # p_i'
                s = scale
                w = 1 # length of occurrence
                z = 0 # partial occurrence
                source_vector = g
                pattern_vector = f

                # Append K_entry to the table
                #TODO make these NoteVector object entries
                self.K[self.flat.notes.index(f.start)].append(K_entry(a, b, y, c, s, w, z, source_vector, pattern_vector))

            # Append the last row, denoted \sum{p_i} : the number of rows generated for table K[i]
            a = float("inf")
            b = float("inf")
            c = self.flat.notes.index(f.start) + 1 # i + 1
            s = 0
            w = 0
            # y, z are not initialized in the pseudocode but an KeyError is thrown in S2 without them
            y = None
            z = 0
            source_vector = None
            pattern_vector = None
            self.K[self.flat.notes.index(f.start)].append(K_entry(a, b, y, c, s, w, z, source_vector, pattern_vector))

            # Sort the K table in order {a, b, s} as per his order set "Aleph". Not totally confident in the implications of the sort order here, so it could maybe be wrong.
            self.K[self.flat.notes.index(f.start)].sort(key = lambda x : (x.a, x.b, x.s))



    def compute_intra_vectors(self, source_window = 0, pattern_window = 1, window = 10):
        """
        Computes intra set vectors.
        Returns a list of intra-set vectors sorted lexicographally by (y, x) rather than (x,y)

        # TODO figure out where the user will set windowing
        :int: source_window limits the search space
        :int: pattern_window = 1 for S1 & W1 while in S2 & W2 it can act as a tolerance variable to limit the distance of skipped notes in the pattern
        """

        note_stream = self.flat.notes
        if window == 0:
            window = len(self) # TODO see if you can't put this in the argument as a default
        self.ivs = sorted([NoteVector(note_stream[i], v_j, note_stream) for i in range(len(note_stream)) for v_j in note_stream[i+1 : i+1+window]], key = lambda x: (x.y, x.x))


    def report_Ktable_occurrences(self, results, source):
        occurrences = music21.stream.Stream()
        for r in results:
            # Get the notes of this particular occurrence
            result_stream = music21.stream.Stream()
            ptr = r
            # TODO make backtracking part of a Ktable (entry or table?) class method
            while ptr != None:
                result_stream.insert(ptr.source_vector.end) # use insert for the note to be placed at its proper offset
                if ptr.y == None:
                    first_note = ptr.source_vector.start
                    result_stream.insert(first_note)
                ptr = ptr.y
            # Get the shift vector for this occurrence
            # TODO make this a NoteVector() - but can't currently, because fist note of pattern is not necessarily contained in the same stream as source note
            result_stream.shift = (first_note.offset - self.flat.notes[0].offset, first_note.pitch.ps - self.flat.notes[0].pitch.ps)
            occurrences.append(result_stream)
        return occurrences

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
    """
