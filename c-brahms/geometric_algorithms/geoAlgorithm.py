from collections import namedtuple #for .scores immutable tuple
from pprint import pformat #for repr
from LineSegment import LineSegment
from NoteSegment import NotePointSet
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

class geoAlgorithm(object):
    """
    Generic base class to manage execution of P, S, and W algorithms
    """
    def __init__(self, pattern_input, source_input, settings = DEFAULT_SETTINGS):

        # Update the default settings with user-specified ones so that the user only has to specify non-default parameters.
        self.settings = DEFAULT_SETTINGS
        self.settings.update(settings)

        # Defines self.pattern and self.source
        # If file paths were given, they are stored in the stream derivations
        self.parse_scores(pattern_input, source_input)

        # Defines self.patternPointSet and self.sourcePointSet
        self.pre_process()

        # Define a result generator
        self.results = self.algorithm()

        # Define an occurrences generator
        self.occurrences = (self.process_result(r) for r in self.results)

        # Do something with the occurrences
        self.post_process()

    def parse_scores(self, pattern_input, source_input):
        """
        Defines self.pattern and self.source
        Tests to see if the input is a file path or something else (possibly already parsed scores)

        Stores input file path in the derivation as a music21Object.
        We can run contextSites() on elements within the parsed score stream. It's a generator which finds context sites, but also follows derivation chains!
        So each element in a derivation chain has to implement contextSites() - so use music21Objects in derivation chains!
        """
        try:
            self.pattern = music21.converter.parse(pattern_input)
            self.pattern.derivation.origin = music21.text.TextBox(pattern_input)
            self.pattern.derivation.method = 'music21.converter.parse()'
        except (music21.converter.ConverterException, AttributeError):
            self.pattern = pattern_input
            self.pattern.derivation.method = 'manual'
        self.pattern.id = 'pattern'

        try:
            self.source = music21.converter.parse(source_input)
            self.source.derivation.origin = music21.text.TextBox(source_input)
            self.source.derivation.method = 'music21.converter.parse()'
        except(music21.converter.ConverterException, AttributeError):
            self.source = source_input
            self.source.derivation.method = 'manual'
        self.source.id = 'source'


    def pre_process(self):
        """
        Defines self.alg_input
        Runs all necessary pre-processing common to every algorithm (lexicographic sorting and chord flattening)
        """
        # NotePointSet sets the derivations of new streams on init
        self.patternPointSet = NotePointSet(self.pattern)
        self.patternPointSet.id = 'patternPointSet'
        self.sourcePointSet = NotePointSet(self.source)
        self.sourcePointSet.id = 'sourcePointSet'

    def process_result(self, result):
        return result

    def post_process(self):
        # Colour the score
        for occurrence in self.occurrences:
            for inter_vec in occurrence:
                if self.source.derivation.method != 'manual':
                    inter_vec.noteEnd.derivation.origin.color = self.settings['colour']

        # Name the score
        self.source.metadata = music21.metadata.Metadata()
        self.source.metadata.title = str(self)

    def run(self):
        print("Running algorithm " + str(self)) # Run the algorithm
        self.results = self.algorithm()

        #TODO not necessary? necessary?
        # If no results, return empty stream
        #if len(self.results) == 0:
        #    self.occurrences = music21.stream.Stream()

        # Processing results is necessary as long as output format is non-constant
        # TODO add try except so empty results doesn't crash? Also add an empty-result test case
        self.occurrences = self.process_results()

        if self.__class__.__name__ == "P3":
            self.occurrencesAsShifts = self.occurrences
        else:
            self.occurrencesAsShifts = [o.shift for o in self.occurrences]

        #self.post_process()


    def algorithm(self):
        pass

    def process_results(self):
        pass



    def __repr__(self):
        return "{0}\npattern = {1},\nsource = {2},\nsettings = {3}".format(self.__class__.__name__, self.pattern.derivation, self.source.derivation, self.settings)

class P(geoAlgorithm):

    def pre_process(self):
        super(P, self).pre_process()
        #self.pattern_line_segments = [LineSegment(note.getOffsetBySite(self.pattern.flat.notes), note.pitch.ps, note.duration.quarterLength, note_link=note) for note in self.pattern.flat.notes]
        #self.source_line_segments = [LineSegment(note.getOffsetBySite(self.source.flat.notes), note.pitch.ps, note.duration.quarterLength, note_link=note) for note in self.source.flat.notes]

    def process_results(self):
        """
        Expects a stream of occurrence streams
        """
        pass
        # Find the shifts
        #for r in self.results:
        #    r.shift = (r[0].offset - self.pattern.flat.notes[0].offset, r[0].pitch.ps - self.pattern.flat.notes[0].pitch.ps)
        #return self.results

class SW(geoAlgorithm):
    def pre_process(self):
        super(SW, self).pre_process()
        self.pattern.compute_intra_vectors(window = self.settings['pattern_window'])
        self.source.compute_intra_vectors(window = self.settings['source_window'])
        self.pattern.initialize_Ktables(self.source)

        if isinstance(self.settings['mismatches'], (int, long)):
            ## TODO make it so you can't have threshold and mismatches set
            ## TODO make it so threshold refers to number of notes (add at +1 in alg)
            self.settings['threshold'] = len(self.pattern.flat.notes) - self.settings['mismatches'] - 1 #recall threshold refers to # of pattern vectors matched
        # If threshold has been passed in and intends to be 'max'..
        if self.settings['threshold'] == len(self.pattern.flat.notes):
            self.settings['threshold'] = self.settings['threshold'] - 1

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

