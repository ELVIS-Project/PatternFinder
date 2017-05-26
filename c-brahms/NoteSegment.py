from itertools import groupby # for use in initializing K tables
from fractions import Fraction
from collections import namedtuple # to make a custom Priority Queue
from pprint import pprint, pformat #for K_enry __repr__
from more_itertools import peekable # to peek in the priority queue
import queue # to make a custom Priority Queue
import copy # for link_and_create
import music21
import pdb

class CmpItQueue(queue.PriorityQueue):
    """
    A subclass of PriorityQueue which implements iteration and custom comparators

    Wraps .put(item, False) and .get(False) so that the PQ does not block. This is not a multi-threading application so we want PQ's to throw Full or Empty exceptions rather than blocking.
    """

    queue_item = namedtuple('queue_item', ['sortTuple', 'item'])

    def __init__(self, keyfunc=lambda p: p, maxsize = 0):
        queue.PriorityQueue.__init__(self, maxsize)
        # We expect that keyfunc(item) returns a sortTuple to sort the elements
        self.keyfunc = keyfunc

    def __iter__(self):
        return self

    def next(self):
        try:
            return self.get()
        except queue.Empty:
            raise StopIteration

    def put(self, item):
        # Every item in the queue is a tuple (sortTuple, item)
        ralph = self.queue_item(self.keyfunc(item), item)
        queue.PriorityQueue.put(self, ralph, False)

    def get(self):
        # Return only the item so that PQ covers up the inconvenience of dealing with the sortTuple
        return queue.PriorityQueue.get(self, False).item

class GeometricNote(music21.note.Note):

    # Override music21 sort tuple so that it sorts by offset rather than onset?
    # This would also help to avoid using indices in algorithms SW. 'a' and 'b'
    # could be replaced by the note itself
    def sortTuple():
        pass

    def __add__(self, other_note):
        pass

#TODO make this a generic SortVector class which InterNoteVector inherits?
# Or just get rid of it all together. we only use note vectors within a site
class NoteVector(music21.interval.Interval):
    def __init__(self, *args, **kwargs):
        super(NoteVector, self).__init__(*args, **kwargs)
        self.x = 0
        self.y = self.chromatic.semitones

        self.sortTupleOrder = ['x', 'y']
        self.sortTuple = lambda: tuple(getattr(self, attr) for attr in self.sortTupleOrder)

    # Rich comparisons. Should also make comparisons with ints/floats/tuples possible
    # functools.total_ordering didn't work for some reason. I had vec1 == vec2, and vec1 != vec2 both be true.
    def __eq__(self, other):
        return self.sortTuple() == other

    def __ne__(self, other):
        return self.sortTuple() != other

    def __ge__(self, other):
        return self.sortTuple() >= other

    def __le__(self, other):
        return self.sortTuple() <= other

    def __gt__(self, other):
        return self.sortTuple() > other

    def __lt__(self, other):
        return self.sortTuple() < other

class InterNoteVector(NoteVector):
    def __init__(self, ralph, ralphSite, larry, larrySite, tp_type=1):
        super(InterNoteVector, self).__init__(noteStart=ralph, noteEnd=larry)
        #TODO make all tp_types attributes or functions, freely accessible?
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
            raise ValueError("InterNoteVector tp_type must be initialized with 0, 1, 2, or 3")


        self.tp_type = tp_type
        self.sortTupleOrder.append('tp_type')

        self.noteStartSite = ralphSite
        self.noteStartIndex = ralphSite.index(ralph)
        self.noteEndIndex = larrySite.index(larry)
        self.noteEndSite = larrySite

    def __repr__(self):
        return  ('<'+ str(self.__class__.__name__) + '>'
                + " TYPE {0} (x={1}, y={2}) ".format(self.tp_type, self.x, self.y)
                + " #{0}: {1} --> #{2}: {3}".format(
                    self.noteStartIndex, self.noteStart, self.noteEndIndex, self.noteEnd))

class IntraNoteVector(InterNoteVector):
    def __init__(self, ralph, larry, site):
        self.site = site
        super(IntraNoteVector, self).__init__(ralph, site, larry, site)

class K_entry(object):
    def __init__(self, intra_pattern_vector, intra_database_vector, w=1, y=None, e=0, z=0):
        if (intra_database_vector.x == 0) and (intra_pattern_vector.x == 0):
            scale = 1
        # NOTE here we can decide on the behaviour of note-to-chord and
        # chord-to-note scaling. Should we allow a chord to expand, or a
        # pattern flatten to a chord?
        elif (intra_database_vector.x == 0) or (intra_pattern_vector.x == 0):
            scale = None
        else:
            scale = Fraction(Fraction(intra_database_vector.x), Fraction(intra_pattern_vector.x))

        self.patternVec = intra_pattern_vector
        self.sourceVec = intra_database_vector
        self.scale = scale # For S1, S2
        self.w = w # length of occurrence
        self.y = y # backlink for building occurrences
        # Optionally we can give occurrences an ID so that as they gradually build,
        # we can more easily replace the shorter yields with their longer ones
        self.z = z # occurrence ID

        # TODO save matching_pairs here rather than computing them in process_result
        """
        throws TypeError: "InterNoteVector object is not callable"
        matching_pairs = namedtuple('matching_pairs', ['start', 'end'])._make(
                InterNoteVector(self.patternVec.noteStart, self.patternVec.site,
                    self.noteStart, self.site),
                InterNoteVector(self.patternVec.noteEnd, self.patternVec.site,
                    self.noteEnd, self.site))
        """


    def __repr__(self):
        return ("<NoteSegment.K_entry> with s={0}, w={1}\n".format(self.scale, self.w)
            + "INTRA PATTERN VECTOR {0} ====>\n".format(self.patternVec)
            + "INTRA DATABASE VECTOR {0}\n".format(self.sourceVec)
            # Indent the backlink so it's more readable
            + "WITH BACKLINK:\n    {0}".format(str(self.y).replace('\n', '\n    ')))
        """
        return ("<NoteSegment.K_entry> with s={0}, w={1}, ".format(self.scale, self.w)
                + "INTRA DATABASE VECTOR: "
                + "<IntraNoteVector> TYPE {0} (x={1}, y={2}) ".format(
                    self.tp_type, self.x, self.y)
                + " #{0}: {1} --> #{2}: {3}\n".format(
                    self.noteStartIndex, self.noteStart, self.noteEndIndex, self.noteEnd)
                + "INTRA PATTERN VECTOR: {0}\n".format(self.patternVec)
            # Indent the backlink so it's more readable
            + "WITH BACKLINK:\n    {0}".format(str(self.y).replace('\n', '\n    ')))
        """

class Occurrence(object):
    """
    Wrapper class for occurrences
    """
    pass

class NotePointSet(music21.stream.Stream):
    """
    A container for the notes of a music21 parsed score.
    Pre-processes the data by flattening the chords and sorting the notes.

    Expects a stream to process
    Optionally can be flagged to sort by offset (note release) rather than the default onset (note attack)

    music21.stream.Stream does not allow any required arguments in its __init__, so every argument must be optional.
    """
    def __init__(self, stream=music21.stream.Stream(), offsetSort=False, *args, **kwargs):
        # TODO use stream.mergeElements and then stream.sort(), overriding sortTuples
        def music21Chord_to_music21Notes(chord, site):
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

        super(NotePointSet, self).__init__()
        self.derivation.method = 'NotePointSet()'
        self.derivation.origin = stream

        # Use .flat instead of .recurse() because we want to preserve the nested
        # stream offsets. When we switch to python3 and use music21 v.3, we can use
        # music21Object.getoffsetInHierarchy(), but for now use stream.flat
        note_stream = stream.flat.notes

        # Sorting key for the NotePointSet: sort lexicographicaly by tuples of:
        #    1) either note onset (attack) or note offset (release)
        #    2) note frequency
        #        -- Since this is the most finely-grained pitch information possible,
        #        the list will still be sorted under any subsequent pitch equivalence
        #        (such as pitch class or enharmonic equivalence)
        sort_keyfunc = lambda n: ((n.offset + n.duration.quarterLength, n.pitch.frequency)
                if offsetSort else (n.offset, n.pitch.frequency))

        # Get each note or chord, convert it to a tuple of notes, and sort them by the keyfunc
        new_notes = sorted(
                [note for note_list in
                    [music21Chord_to_music21Notes(n, note_stream) if n.isChord
                        # Don't use copy.deepcopy(n) or else it will lose the offset info
                        else (n,) for n in note_stream]
                    for note in note_list],
                key=sort_keyfunc)

        # Make sure to turn off stream.autoSort, since streams automatically sort on insert by
        # an internal sortTuple which prioritizes note onset (attack)
        self.autoSort = False
        for n in new_notes:
            self.insert(n)

    def compute_intra_vectors(self, window = 1):
        """
        Computes the set of IntraSetVectors in a NotePointSet.

        :int: window refers to the "reach" of any intra vector. It is the maximum
        number of intervening notes inbetween the start and end of an intra-vector.
        """
        # NOTE would be nice to use iterators instead of indices, couldn't get it to work
        self.intra_vectors = [IntraNoteVector(self[i], end, self)
                for i in range(len(self))
                for end in self[i+1 : i+1+window]]

    # TODO make this a part of geoAlgorithm since it's really about a pattern and a source, not just any segment stream.
    def initialize_KtablesOld(self, source):
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

        if window == 0:
            window = len(self) # TODO see if you can't put this in the argument as a default
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

#K_entry = namedtuple('K_entry', ['a', 'b', 'y', 'c', 's', 'e', 'w', 'z', 'source_vector', 'pattern_vector'])
#TODO make a K_entry just an extended NoteVector?
class K_entryOld():
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

