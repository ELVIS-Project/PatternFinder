from collections import namedtuple #for .scores immutable tuple
from pprint import pformat #for repr
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
    note_list = []
    for pitch in chordy.pitches:
        note = music21.note.Note(pitch)
        note.offset = element.getOffsetBySite(stream[0])
        note.duration = element.duration
        note.didBelongToAChord = True
        note.original = element

        note_list.append(offset)
        note_list.append(note)
    return note_list

class geoAlgorithm(object):
    def __init__(self, pattern_score, source_score, settings = DEFAULT_SETTINGS):
        # Settings
        self.settings = DEFAULT_SETTINGS
        self.settings.update(settings) # So not all keywords must be specified on call
        self.scores = namedtuple("Scores", ['pattern', 'source'])._make((pattern_score, source_score))

        self.original_pattern = music21.converter.parse(pattern_score)
        self.original_source = music21.converter.parse(source_score)
        ### Get rid of the chords but keep the original score

        self.source = music21.stream.Stream(music21.stream.Part())
        self.pattern = music21.stream.Stream(music21.stream.Part())

        for stream in ((self.original_source.flat.notes, self.source), (self.original_pattern.flat.notes, self.pattern)):
            #use .flat.notes instead of .recurse() because note.getOffsetByHierarchy is only in music 21 version 3
            i = 0
            for element in stream[0]:
                if element.isChord:
                    for pitch in element.pitches:
                        note = music21.note.Note(pitch)
                        note.offset = element.getOffsetBySite(stream[0])
                        note.duration = element.duration
                        note.didBelongToAChord = True
                        note.original = element

                        # Index
                        note.index = i
                        i += 1
                        stream[1].insert(note)
                else:
                    # Index
                    element.index = i
                    i += 1

                    element.didBelongToAChord = False
                    element.original = element
                    stream[1].insert(element.getOffsetBySite(stream[0]), element)

        # TODO use two streams one for orig, one for not, have notes point back to their respective chords?
        # Now we can make note sets
        self.pattern = NoteSegment.NoteSegments(self.pattern)
        self.source = NoteSegment.NoteSegments(self.source)

    def run(self):
        self.pattern.lexicographic_sort()
        self.source.lexicographic_sort()
        # don't run the algorithm here or you'll miss out on other preprocessing

    def colour_score(self, occurrences):
        for n in occurrences.flat.notes:
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

    def __repr__(self):
        # TODO add scores tuple
        return "{0}(\nscores = {1},\nsettings = {2})".format(self.__class__, self.scores, self.settings)


class geoAlgorithmSW(geoAlgorithm):
    def run(self):
        super(geoAlgorithmSW, self).run() #preprocess

        # Preprocess
        self.pattern.compute_intra_vectors(self.settings['window'])
        self.source.compute_intra_vectors(self.settings['window'])
        # TODO ktable initialization shouldn't be repeated for diff. algys, it should be done once and made part of the score?
        self.pattern.initialize_Ktables(self.source)

        # Algorithm returns a list of K_rows
        self.results = self.algorithm()
        # Process_results returns a filtered stream of matched notes in the source
        self.occurrences = self.process_results(self.results)

        self.colour_score(self.occurrences)

    def process_results(self, results):
        if self.settings['scale'] != "all":
            results = filter(lambda x: x.s == self.settings['scale'], results)

        occurrences = music21.stream.Stream()
        for r in results:
            # Get the notes of this particular occurrence
            result_stream = music21.stream.Stream()
            ptr = r
            # TODO make backtracking part of a Ktable (entry or table?) class method
            while ptr != None:
                result_stream.insert(ptr.source_vector.end.getOffsetBySite(self.source.flat.notes), ptr.source_vector.end) # use insert for the note to be placed at its proper offset
                if ptr.y == None:
                    first_note = ptr.source_vector.start
                    result_stream.insert(first_note.getOffsetBySite(self.source.flat.notes), first_note)
                ptr = ptr.y
            # Get the shift vector for this occurrence
            # TODO make this a NoteVector() - but can't currently, because fist note of pattern is not necessarily contained in the same stream as source note
            result_stream.shift = (first_note.offset - self.pattern.flat.notes[0].offset, first_note.pitch.ps - self.pattern.flat.notes[0].pitch.ps)
            occurrences.append(result_stream)

        return occurrences
