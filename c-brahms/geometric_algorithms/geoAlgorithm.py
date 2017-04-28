from collections import namedtuple #for .scores immutable tuple
from pprint import pformat #for repr
from LineSegment import LineSegment
import NoteSegment
import copy
import music21
import pdb

DEFAULT_SETTINGS = {
        'pattern_window' : 1,
        '%pattern_window' : 1,
        'source_window' : 5,
        'scale' : "all",
        'colour' : "red",
        'threshold' : 'max',
        '%threshold' : 1,
        'mismatches' : 'min',
        'segment' : False,
        'overlap' : True,
        'parsed_input' : False,
        'runOnInit' : True}

def get_notesegments_from_score(source_score):
    #original_pattern = music21.converter.parse(pattern_score) already passed by get_pattern_from_fugue
    #original_pattern = pattern_score
    original_source = music21.converter.parse(source_score)

    ### Get rid of the chords but keep the original score
    #pattern = music21.stream.Stream(music21.stream.Part())
    source = music21.stream.Stream(music21.stream.Part())

    print("GeoAlgorithm: removing chords...")
    #use .flat.notes instead of .recurse() because note.getOffsetByHierarchy is only in music 21 version 3
    i = 0
    for element in original_source.flat.notes:
        print(element)
        if element.isChord:
            for pitch in element.pitches:
                note = music21.note.Note(pitch)
                note.offset = element.getOffsetBySite(original_source.flat.notes)
                note.duration = element.duration
                note.didBelongToAChord = True
                note.original = element

                # Index
                note.index = i
                i += 1
                source.insert(note)
        else:
            # Index
            element.index = i
            i += 1

            element.didBelongToAChord = False
            element.original = element
            source.insert(element.getOffsetBySite(original_source.flat.notes), element)
    return ((original_source, source))

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
    """
    Generic base class to manage execution of P, S, and W algorithms
    """
    def __init__(self, pattern_score, source_score, settings = DEFAULT_SETTINGS):
        self.settings = DEFAULT_SETTINGS
        self.settings.update(settings) # So that not all keywords must be specified on call
        self.scores = namedtuple("Scores", ['pattern', 'source'])._make((pattern_score, source_score))

        print("GeoAlgorithm: preprocessing...")
        self.pre_process()
        print("GeoAlgorithm: done preprocessing")

        if self.settings['runOnInit']:
            self.run()

    def run(self):
        print("Running algorithm " + str(self)) # Run the algorithm
        self.results = self.algorithm()

        #TODO not necessary? necessary?
        # If no results, return empty stream
        #if len(self.results) == 0:
        #    self.occurrences = music21.stream.Stream()

        # Processing results is necessary as long as output format is non-constant
        self.occurrences = self.process_results()

        if self.__class__.__name__ == "P3":
            self.occurrencesAsShifts = self.occurrences
        else:
            self.occurrencesAsShifts = [o.shift for o in self.occurrences]

        self.post_process()


    def pre_process(self):
        print("GeoAlgorithm: parsing...")
        if self.settings['parsed_input'] is False:
            self.original_pattern = music21.converter.parse(self.scores.pattern)
            self.original_source = music21.converter.parse(self.scores.source)
        else:
            self.original_pattern = self.scores.pattern
            self.original_source = self.scores.source

        ### Get rid of the chords but keep the original score
        self.source = music21.stream.Stream(music21.stream.Part())
        self.pattern = music21.stream.Stream(music21.stream.Part())

        print("GeoAlgorithm: removing chords...")
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
        print("GeoAlgorithm: making NoteSegments...")
        self.pattern = NoteSegment.NoteSegments(self.pattern)
        self.source = NoteSegment.NoteSegments(self.source)

        # Sort source and pattern 
        # Should sort another way other than changing the priorities. what a waste of computation
        print("GeoAlgorithm: sorting...")
        self.pattern.lexicographic_sort()
        self.source.lexicographic_sort()

    def algorithm(self):
        pass

    def process_results(self):
        pass

    def post_process(self):
        # Colour the score
        if self.occurrences is None:
            return
        for n in self.occurrences.flat.notes:
            n.original.color = self.settings['colour']

        # Name the score
        self.original_source.metadata = music21.metadata.Metadata()
        self.original_source.metadata.title = str(self)


    def __repr__(self):
        return "{0}\npattern = {1},\nsource = {2},\nsettings = {3}".format(self.__class__.__name__, self.scores.pattern, self.scores.source, self.settings)

class P(geoAlgorithm):

    def pre_process(self):
        super(P, self).pre_process()
        self.pattern_line_segments = [LineSegment(note.getOffsetBySite(self.pattern.flat.notes), note.pitch.ps, note.duration.quarterLength, note_link=note) for note in self.pattern.flat.notes]
        self.source_line_segments = [LineSegment(note.getOffsetBySite(self.source.flat.notes), note.pitch.ps, note.duration.quarterLength, note_link=note) for note in self.source.flat.notes]

    def process_results(self):
        """
        Expects a stream of occurrence streams
        """
        # Find the shifts
        for r in self.results:
            r.shift = (r[0].offset - self.pattern.flat.notes[0].offset, r[0].pitch.ps - self.pattern.flat.notes[0].pitch.ps)
        return self.results

class SW(geoAlgorithm):
    def pre_process(self):
        super(SW, self).pre_process()
        self.pattern.compute_intra_vectors(self.settings['pattern_window'])
        self.source.compute_intra_vectors(self.settings['source_window'])
        self.pattern.initialize_Ktables(self.source)

        if isinstance(self.settings['mismatches'], (int, long)):
            ## TODO make it so you can't have threshold and mismatches set
            ## TODO make it so threshold refers to number of notes (add at +1 in alg)
            self.settings['threshold'] = len(self.pattern.flat.notes) - self.settings['mismatches'] - 1 #recall threshold refers to # of pattern vectors matched

    def process_results(self):
        #TODO clean up chain flattening
        def flatten_chain(K_row, chain=None):
            """
            Call this with the final K_row in the chain
            """
            chain = music21.stream.Stream()
            if K_row.y == None:
                chain.insert(K_row.source_vector.start)
                return chain
            else:
                chain.insert(K_row.source_vector.end)
                return flatten_chain(K_row.y, chain)

        ### Filtering. TEMPORARY FIX. TODO you should make separate subclasses?

        occurrences = music21.stream.Stream()
        for r in self.results:
            # Get the notes of this particular occurrence
            result_stream = music21.stream.Stream()
            ptr = r
            # TODO make backtracking part of a Ktable (entry or table?) class method
            ## TODO make this a tail-recursive function
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

