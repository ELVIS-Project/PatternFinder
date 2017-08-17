import queue # to make a custom Priority Queue
import music21
import pdb

from itertools import groupby # for use in initializing K tables
from fractions import Fraction # for scale in K entries
from collections import namedtuple # to make a custom Priority Queue

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

# @TODO make this a generic SortVector class which InterNoteVector inherits?
# Or just get rid of it all together. we only use note vectors within a site
class NoteVector(music21.interval.Interval):
    def __init__(self, y_func, *args, **kwargs):
        super(NoteVector, self).__init__(*args, **kwargs)
        self.x = 0
        self.y = y_func(self)

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
    """
    Each InterNoteVector is a shift from a pattern note to a source note
    We subclass NoteVector to inherit rich comparisons and a SortTuple mechanism

    We use the y_func to determine the height difference between notes (e.g. if we want don't want
    enharmonic equivalence, use base40)
    """
    # y_func should get the default from SETTINGS. but we include a default here because
    # we use InterNoteVector in K_entry to compute matching pairs.
    def __init__(self, ralph, ralphSite, larry, larrySite, y_func=lambda x: x.chromatic.semitones, tp_type=1):
        super(InterNoteVector, self).__init__(noteStart=ralph, noteEnd=larry, y_func=y_func)
        #TODO calculate all tp_types and make them available as attributes?
        if tp_type == 0:
            # source.onset - pattern.offset
            self.x = (larry.getOffsetBySite(larrySite) -
                    (ralph.getOffsetBySite(ralphSite) + ralph.duration.quarterLength))
        elif tp_type == 1:
            # source.onset - pattern.onset
            self.x = larry.getOffsetBySite(larrySite) - ralph.getOffsetBySite(ralphSite)
        elif tp_type == 2:
            # source.offset - pattern.offset
            self.x = ((larry.getOffsetBySite(larrySite) + larry.duration.quarterLength) -
                    (ralph.getOffsetBySite(ralphSite) + ralph.duration.quarterLength))
        elif tp_type == 3:
            # source.offset - pattern.onset
            self.x = ((larry.getOffsetBySite(larrySite) + larry.duration.quarterLength)
                    - ralph.getOffsetBySite(ralphSite))
        else:
            raise ValueError("InterNoteVector tp_type must be initialized with 0, 1, 2, or 3")


        # Sort an InterNoteVector by (x, y, tp_type)
        self.tp_type = tp_type
        self.sortTupleOrder.append('tp_type')

        self.noteStartSite = ralphSite
        self.noteStartIndex = ralphSite.index(ralph)
        self.noteEndIndex = larrySite.index(larry)
        self.noteEndSite = larrySite

    def __repr__(self):
        # @TODO This does not have to be this ugly... Improve the note.Note repr!!!
        measure_start = self.noteStart.getContextByClass('Measure')
        measure_end = self.noteEnd.getContextByClass('Measure')

        try:
            measure_info_start = "({0} of m.{1})".format(
                self.noteStart.offset,
                measure_start.number)
        except AttributeError:
            measure_info_start = "no measure info"

        try:
            measure_info_end = "({0} of m.{1})".format(
                    self.noteEnd.offset,
                    measure_end.number)
        except AttributeError:
            measure_info_end = "no measure info"

        return ('<' + str(self.__class__.__name__) + '>'
                + " TP {0} (x={1}, y={2}) ".format(self.tp_type, self.x, self.y)
                + " #{0} PART {1} {2} {3} -->".format(
                    self.noteStartIndex, self.noteStart.getContextByClass('Part').partName,
                    self.noteStart.pitch.nameWithOctave, measure_info_start)
                + " #{0} PART {1} {2} {3}".format(
                    self.noteEndIndex, self.noteEnd.getContextByClass('Part').partName,
                    self.noteEnd.pitch.nameWithOctave, measure_info_end))

class IntraNoteVector(InterNoteVector):
    def __init__(self, ralph, larry, site, y_func):
        self.site = site
        super(IntraNoteVector, self).__init__(ralph, site, larry, site, y_func)

class K_entry(object):
    """
    K_entries are
    """
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

    def __repr__(self):
        return ("<NoteSegment.K_entry> with s={0}, w={1}\n".format(self.scale, self.w)
            + "INTRA PATTERN VECTOR {0}\n".format(self.patternVec)
            + "INTRA DATABASE VECTOR {0}\n".format(self.sourceVec)
            # Indent the backlink so it's more readable
            + "WITH BACKLINK:\n    {0}".format(str(self.y).replace('\n', '\n    ')))

def music21Chord_to_music21Notes(chord):
    """
    For internal use in NotePointSet()

    CHORD TO LIST OF NOTES FOR USE IN music21.stream.insert()
    For serious flattening of the score into a 2-d plane of horizontal line segments.
    music21.note.Note and music21.chord.Chord subclass the same bases,
    so in theory it shoud look something like this...

    NOTE: this will screw up the coloring since music21 doesn't support coloring just
    one note of a chord (I don't think?), so as compromise I'll just color the whole chord.
    """
    note_list = []
    for pitch in chord.pitches:
        note = music21.note.Note(pitch)

        # Music21Object.mergeAttributes gets the 'id' and 'group' attributes
        note.mergeAttributes(chord)

        # note essentials
        note.duration = chord.duration
        note.offset = chord.offset

        note_list.append(note)

        note.derivation.origin = chord
        note.derivation.method = 'chord_to_notes'
    return note_list

class NotePointSet(music21.stream.Stream):
    """
    A container for the notes of a music21 parsed score.
    Pre-processes the data by flattening the chords and sorting the notes.

    Expects a stream to process
    Optionally can be flagged to sort by offset (note release) rather than the default onset (note attack)

    music21.stream.Stream does not allow any required arguments in its __init__, so every argument must be optional.
    """
    def __init__(self, score=music21.stream.Stream(), offsetSort=False, *args, **kwargs):
        super(NotePointSet, self).__init__()
        # Set the derivation for this PointSet
        self.derivation.method = 'NotePointSet()'
        self.derivation.origin = score

        # If we have None input, return an empty stream
        if not score:
            return

        # Sorting key for the NotePointSet: sort lexicographicaly by tuples of:
        #    1) either note onset (attack) or note offset (release)
        #    2) note frequency
        #        -- Since this is the most finely-grained pitch information possible,
        #        the list will still be sorted under any subsequent pitch equivalence
        #        (such as pitch class or enharmonic equivalence)
        sort_keyfunc = lambda n: ((n.offset + n.duration.quarterLength, n.pitch.frequency)
                if offsetSort else (n.offset, n.pitch.frequency))

        # Get each note or chord, convert it to a tuple of notes, and sort them by the keyfunc
        new_notes = []
        for note in score.flat.notes:
            to_add = music21Chord_to_music21Notes(note)
            # Use .original_note instead of derivation chains. It has to be consistent:
            # you can't be checking different derivations for notes which came from chords
            # versus notes which were not derived. If for example a source was transposed
            # (like in the test cases), the derivation will be non-empty, which screws up
            # the decision making for occurrences later on.
            for n in to_add:
                n.original_note_id = note.id
            new_notes.extend(to_add)
        new_notes.sort(key=sort_keyfunc)

        # Make sure to turn off stream.autoSort, since streams automatically sort on insert by
        # an internal sortTuple which prioritizes note onset (attack)
        self.autoSort = False
        for n in new_notes:
            self.insert(n)

