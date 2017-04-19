import NoteSegment
import copy
import music21
import pdb

DEFAULT_SETTINGS = {'window' : 5, 'scale' : "all", 'colour' : "red", 'threshold' : 2}

def music21Chord_to_music21Notes(chordy):
    """
    CHORD TO NOTE GENERATOR
    For serious flattening of the score into a 2-d plane of horizontal line segments.
    music21.note.Note and music21.chord.Chord have the same bases, so in theory it shoud look something like this...

    NOTE: this will screw up the coloring since music21 doesn't support coloring one note of a chord (i don't think?), so as compromise i'll just color the whole chord.

    N.T.S.: it does not seem you can do music21.insert(<generator expression>). think of a slick way?
    """
    for pitch in chordy.pitches:
        note = music21.note.Note(pitch)
        note.offset = chordy.offset
        note.duration = chordy.duration
        note.site = chordy.site
        note.didBelongToAChord = True
        yield note

class geoAlgorithm(object):
    def __init__(self, pattern_score, source_score, settings = DEFAULT_SETTINGS):
        self.settings = settings

        self.original_pattern = music21.converter.parse(pattern_score)
        self.original_source = music21.converter.parse(source_score)
        ### Get rid of the chords but keep the original score

        self.source = music21.stream.Stream(music21.stream.Part())
        self.pattern = music21.stream.Stream(music21.stream.Part())

        for stream in ((self.original_source.flat.notes, self.source), (self.original_pattern.flat.notes, self.pattern)):
            #use .flat.notes instead of .recurse() because note.getOffsetByHierarchy is only in music 21 version 3
            for element in stream[0]:
                if element.isChord:
                    for pitch in element.pitches:
                        note = music21.note.Note(pitch)
                        note.offset = element.getOffsetBySite(stream[0])
                        note.duration = element.duration
                        note.didBelongToAChord = True
                        note.original = element
                        stream[1].insert(note)
                else:
                    element.didBelongToAChord = False
                    element.original = element
                    stream[1].insert(element.getOffsetBySite(stream[0]), element)

        """
        self.pattern = copy.deepcopy(self.original_pattern)
        self.source = copy.deepcopy(self.original_source)

        for stream in (self.source, self.pattern):
            for element in stream.flat.notes:
                if element.isChord:
                    for pitch in element.pitches:
                        note = music21.note.Note(pitch)
                        note.offset = element.offset
                        note.duration = element.duration
                        note.didBelongToAChord = True
                        stream.insert(note)
                    # Recall: stream.flat.notes is a new temporary stream. you have to remove the note by ID
                    stream.remove(stream.flat.notes.getElementById(element.id), recurse=True)
                else:
                    #otherwise, this must be a note
                    element.didBelongToAChord = False
        """

        # Append extra notes as per pseudocode
        # TODO figure out an indexing work around so you don't need this
        # affects: k_table initialization, compute_intra_vectors, S2 commenting
        #self.pattern.append(music21.note.Note())
        #self.source.append(music21.note.Note())

        # TODO use two streams one for orig, one for not, have notes point back to their respective chords?
        # Now we can make note sets
        self.pattern = NoteSegment.NoteSegments(self.pattern)
        self.source = NoteSegment.NoteSegments(self.source)

    def run(self):
        self.pattern.lexicographic_sort()
        self.source.lexicographic_sort()
        # don't run the algorithm here or you'll miss out on other preprocessing

    def post_process(self):
        for n in self.results.flat.notes:
            n.original.color = self.settings['colour']

    def algorithm(self):
        """
        Input:
        :NoteSegments: pattern
        :NoteSegments: pattern

        Output:
        :music21.stream.Stream: of notes in the source which count as a similar "occurrence" as defined in Lemstrom's papers and corresponding to each individual algorithm.
        For each :stream: occurrence within :stream: results, an attribute :tuple: results.occurrence.shift should also be outputed. This tuple just gives the (x,y) translation of the pattern in order to line up with the source occurrence.
        """
        pass


class geoAlgorithmSW(geoAlgorithm):
    def run(self):
        super(geoAlgorithmSW, self).run() #preprocess
        self.pattern.compute_intra_vectors(self.settings['window'])
        self.source.compute_intra_vectors(self.settings['window'])
        self.results = self.algorithm()
        self.post_process()
        return self.results
