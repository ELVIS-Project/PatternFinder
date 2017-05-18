from itertools import groupby # for use in initializing K tables
from fractions import Fraction
from collections import namedtuple # to make a custom Priority Queue
from pprint import pprint, pformat #for K_enry __repr__
import Queue # to make a custom Priority Queue
import copy # for link_and_create
import numpy as np
import pandas as pd
import music21
import pdb

class CmpItQueue(Queue.PriorityQueue):
    """
    A subclass of PriorityQueue which implements iteration and custom comparators

    Wraps .put(item, False) and .get(False) so that the PQ does not block. This is not a multi-threading application so we want PQ's to throw Full or Empty exceptions rather than blocking.
    """

    queue_item = namedtuple('queue_item', ['sortTuple', 'item'])

    def __init__(self, keyfunc, maxsize = 0):
        Queue.PriorityQueue.__init__(self, maxsize)
        # We expect that keyfunc(item) returns a sortTuple to sort the elements
        self.keyfunc = keyfunc

    def __iter__(self):
        return self

    def next(self):
        try:
            return self.get()
        except Queue.Empty:
            raise StopIteration

    def put(self, item):
        # Every item in the queue is a tuple (sortTuple, item)
        ralph = self.queue_item(self.keyfunc(item), item)
        Queue.PriorityQueue.put(self, ralph, False)

    def get(self):
        # Return only the item so that PQ covers up the inconvenience of dealing with the sortTuple
        return Queue.PriorityQueue.get(self, False).item

#K_entry = namedtuple('K_entry', ['a', 'b', 'y', 'c', 's', 'e', 'w', 'z', 'source_vector', 'pattern_vector'])
#TODO make a K_entry just an extended NoteVector?
class K_entry():
    def __init__(self, p_vec, s_vec, K_index = 0, finalRow = False):

        if not finalRow:
            # Compute scale
            if p_vec.x == 0 and s_vec.x == 0:
                scale = 1
            elif (p_vec.x == float("inf") and s_vec.x == float("inf")) or p_vec.x == 0 or s_vec.x == 0:
                scale = None
            else:
                # Fraction(num, denom) only accepts integers as arguments, so you need to convert source_vec and pattern_vec first
                scale = Fraction(Fraction(s_vec.x), Fraction(p_vec.x))

            # K_entry data
            a = s_vec.site.index(s_vec.start)
            b = s_vec.site.index(s_vec.end)
            c = p_vec.site.index(p_vec.end) # p_i'
            s = scale # For S1, S2
            w = 1 # length of occurrence
            source_vector = s_vec
            pattern_vector = p_vec
        else:
            a = float("inf")
            b = float("inf")
            c = K_index + 1 # i + 1
            s = 0
            w = 0
            # y, z are not initialized in the pseudocode but an KeyError is thrown in S2 without them TODO make defaults in the K_entry __init__
            source_vector = None
            pattern_vector = None

        y = None # backlink for building occurrences
        e = 0 # For W1, W2
        z = 0 # partial occurrence
        self.a, self.b, self.c, self.s, self.y, self.e, self.w, self.z, self.source_vector, self.pattern_vector = a, b, c, s, y, e, w, z, source_vector, pattern_vector

    def __repr__(self):
        return pformat(self.__dict__)

class GeometricNote(music21.note.Note):

    def __add__(self, other_note):
        pass

class NoteVector2(music21.interval.Interval):
    def __init__(self, *args, **kwargs):
        super(NoteVector2, self).__init__(*args, **kwargs)
        self.x = 0
        self.y = self.chromatic.semitones

    def __cmp__(self, other_vector):
        """
        A lexicographic comparison function. For example, [1,42] < [2,3] and [2,1] < [3,22]
        """
        if (self.x, self.y) < (other_vector.x, other_vector.y):
            return -1
        elif (self.x, self.y) > (other_vector.x, other_vector.y):
            return 1
        return 0


class InterNoteVector(NoteVector2):
    def __init__(self, ralph, ralphSite, larry, larrySite, tp_type=1):
        super(InterNoteVector, self).__init__(noteStart=ralph, noteEnd=larry)
        if tp_type == 0:
            # source.onset - pattern.offset
            self.x = larry.getOffsetBySite(larrySite) - (ralph.getOffsetBySite(ralphSite) + ralph.duration.quarterLength)
        elif tp_type == 1:
            # source.onset - pattern.onset
            self.x = larry.getOffsetBySite(larrySite) - ralph.getOffsetBySite(ralphSite)
        elif tp_type == 2:
            # source.offset - pattern.offset
            self.x = (larry.getOffsetBySite(larrySite) + larry.duration.quarterLength) - (ralph.getOffsetBySite(ralphSite) + ralph.duration.quarterLength)
        elif tp_type == 3:
            # source.offset - pattern.onset
            self.x = (larry.getOffsetBySite(larrySite) + larry.duration.quarterLength) - ralph.getOffsetBySite(ralphSite)
        else:
            raise ValueError("InterNoteVector tp_type must be 0, 1, 2, or 3")

        self.tp_type = tp_type
        self.noteStartSite = ralphSite
        self.noteStartIndex = ralphSite.index(ralph)
        self.noteEndIndex = larrySite.index(larry)
        self.noteEndSite = larrySite

    def __repr__(self):
        return super(InterNoteVector, self).__repr__() + " TYPE {0} (x={1}, y={2}) ".format(self.tp_type, self.x, self.y) + " #{0}: {1} --> #{2}: {3}".format(self.noteStartIndex, self.noteStart, self.noteEndIndex, self.noteEnd)

class IntraNoteVector(InterNoteVector):
    def __init__(self, ralph, larry, site):
        super(IntraNoteVector, self).__init__(self, ralph, site, larry, site)

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

class NotePointSet(music21.stream.Stream):
    """
    A container for the notes of a music21 parsed score.
    Pre-processes the data by flattening the chords and sorting the notes.

    Expects a stream to process
    Optionally can be flagged to sort by offset (note release) rather than the default onset (note attack)

    music21.stream.Stream does not allow any required arguments in its __init__, so every argument must be optional.
    """
    def __init__(self, stream=music21.stream.Stream(), offsetSort=False, *args, **kwargs):
        super(NotePointSet, self).__init__()
        self.derivation.method = 'NotePointSet()'
        self.derivation.origin = stream

        note_stream = stream.flat.notes

        # Sorting key for the NotePointSet: sort lexicographicaly by tuples
        # 1) either note onset (attack) or note offset (release)
        # 2) note frequency. Since this is the most finely-grained pitch information possible, the list will still be sorted under any subsequent pitch equivalence (such as pitch class or enharmonic equivalence)
        sort_keyfunc = lambda n: (n.offset + n.duration.quarterLength, n.pitch.frequency) if offsetSort else (n.offset, n.pitch.frequency)

        # Get each note or chord, convert it to a tuple of notes, and sort them by the keyfunc
        new_notes = sorted([note for note_list in [self.music21Chord_to_music21Notes(n, note_stream) if n.isChord else (n,) for n in note_stream] for note in note_list], key=sort_keyfunc)

        # Make sure to turn off stream.autoSort, since streams automatically sort on insert by an internal sortTuple which prioritizes note onset (attack)
        self.autoSort = False
        for n in new_notes:
            self.insert(n)

    def music21Chord_to_music21Notes(self, chord, site):
        """
        CHORD TO LIST OF NOTES FOR USE IN music21.stream.insert()
        For serious flattening of the score into a 2-d plane of horizontal line segments.
        music21.note.Note and music21.chord.Chord subclass the same bases, so in theory it shoud look something like this...

        NOTE: this will screw up the coloring since music21 doesn't support coloring just one note of a chord (i don't think?), so as compromise i'll just color the whole chord.
        """
        note_list = []
        for pitch in chord.pitches:
            note = music21.note.Note(pitch)

            # Music21Object.mergeAttributes gets the 'id' and 'group' attributes
            note.mergeAttributes(chord)

            # note essentials
            note.duration = chord.duration

            note_list.append(note)

            note.derivation.origin = chord
            note.derivation.method = 'chord_to_notes'
        return note_list

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
        self.autoSort = False
        for n in self.flat.notes:
            n.priority = int(n.pitch.ps) # priority values must be integers, and pitch.ps returns a float. This may lead to some buggy issues with quartertones, since two notes a quarter-tone a part will be treated as identical due to truncation.
        self.autoSort = True

    def flatten_chords(self):
        def music21Chord_to_music21Notes(chord, site):
            """
            CHORD TO LIST OF NOTES FOR USE IN music21.stream.inser()
            For serious flattening of the score into a 2-d plane of horizontal line segments.
            music21.note.Note and music21.chord.Chord subclass the same bases, so in theory it shoud look something like this...

            NOTE: this will screw up the coloring since music21 doesn't support coloring one note of a chord (i don't think?), so as compromise i'll just color the whole chord.
            """
            note_list = []
            for pitch in chord.pitches:
                note = music21.note.Note(pitch)

                # note essentials
                note.offset = chord.getOffsetBySite(site)
                note.duration = chord.duration

                # our modifications
                note.link = chord.link
                note.didBelongToAChord = True

                # music21.stream.insert() expects [offset #1, note #1, offset #2, ...]
                note_list.append(offset)
                note_list.append(note)
            return note_list

        # Use .flat instead of .recurse() because you want to preserve the nested stream offsets. You can use .getOffsetInHierarchy() in music21 v.3 but we are using v.2 currently
        for element in self.flat.notes:
            if element.isChord:
                self.insert(music21Chord_to_music21Notes(element, self.flat.notes))
                self.remove(element, recurse=True)
            else:
                element.didBelongToAChord = False

    # TODO make this a part of geoAlgorithm since it's really about a pattern and a source, not just any segment stream.
    def initialize_Ktables(self, source):
        """
        K-table data structure used in algorithms S1-2, W1-2
        'self' should be a pattern that is to be searched for in asource

        Requires that self, source intra_vectors have already been initialized with their desired windowing
        """

        """
##
        print("INITIALIZING KTABLES ....\n")
        print("PATTER IVS ")
        print(len(self.ivs))
        print("SOURCE IVS ")
        print(len(source.ivs))
##
        """

        # There is one K table per note in the pattern
        # TODO make the K table a class so you can have a PQ in it; this will make the algorithm code cleaner (no need to index PQ's)
        self.K = [[] for note in self.flat.notes]

        # Dict comprehension using groupby in order to easily access database vectors based on their pitch translations (y values)
        intra_database_vectors = {key : list(g) for key, g in groupby(source.ivs, lambda x: x.y)}

        # sort and group pattern vectors by the indices of their starting note
        keyfunc = lambda x: x.site.index(x.start)
        self.ivs.sort(key=keyfunc)
        for K_index, group in groupby(self.ivs, keyfunc):
            self.K[K_index] = [K_entry(p_vec, s_vec) for p_vec in group for s_vec in intra_database_vectors.get(p_vec.y) if K_entry(p_vec, s_vec).s is not None]

            # Append the last row, denoted \sum{p_i} : the number of rows generated for table K[i]
            self.K[K_index].append(K_entry(None, None, K_index, finalRow = True))

            # Sort the K table in order {a, b, s} as per his order set "Aleph". Not totally confident in the implications of the sort order here, so it could maybe be wrong.
            self.K[K_index].sort(key = lambda x : (x.a, x.b, x.s))



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
