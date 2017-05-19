from collections import namedtuple #for .scores immutable tuple
from pprint import pformat #for repr
from LineSegment import LineSegment
from NoteSegment import NotePointSet
import NoteSegment
import copy
import music21
import pdb

# TODO measure total runtime with timeit (as a ratio of # of notes), store in an attribute like self.algorithmRunTime?

# TODO maybe have separate user and algorithm settings. this would allow for translations like..
# pattern_accuracy : 'all' --> threshold : len(pattern)
# pattern_accuracy : 'max' --> threshold = len(max(self.results, key=lambda x: len(x)))
DEFAULT_SETTINGS = {
        'pattern_window' : 1,
        '%pattern_window' : 1,
        'source_window' : 5,
        'scale' : "all",
        'colour' : "red",
        'threshold' : 'all',
        '%threshold' : 1,
        'mismatches' : 'min',
        'segment' : False,
        'overlap' : True,
        'parsed_input' : False,
        'runOnInit' : True}

class GeoAlgorithm(object):
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

        # Run the algorithm, filter the occurrences, define an occurrence generator.
        self.occurrences = (self.process_result(r) for r in self.algorithm() if self.filter_occurrence(self.process_result(r)))

        # Do something with the occurrences
        #self.post_process()

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
            self.pattern.derivation.method = 'pre-parsed'
        self.pattern.id = 'pattern'

        try:
            # Parse
            self.source = music21.converter.parse(source_input)
            # Set the derivation
            self.source.derivation.origin = music21.text.TextBox(source_input)
            self.source.derivation.method = 'music21.converter.parse()'
            # Set the score title
            self.source.metadata = music21.metadata.Metadata()
            self.source.metadata.title = source_input
        except(music21.converter.ConverterException, AttributeError):
            self.source = source_input
            self.source.derivation.method = 'pre-parsed'
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

    def process_result(self, r):
        return r

    def filter_occurrence(self, occurrence):
        if self.settings['threshold'] == 'all':
            threshold = len(self.patternPointSet)
        else:
            threshold = self.settings['threshold']
        return len(occurrence) >= threshold

    def post_process(self):
        # Colour the score
        self.check = []
        if self.source.derivation.method != 'manual':
            for occurrence in self.occurrences:
                self.check.append(occurrence)
                for inter_vec in occurrence:
                    if inter_vec.noteEnd.derivation.origin:
                        inter_vec.noteEnd.derivation.origin.color = self.settings['colour']
                    else:
                        inter_vec.noteEnd.color = self.settings['colour']

    def __repr__(self):
        return "{0}\npattern = {1},\nsource = {2},\nsettings = {3}".format(self.__class__.__name__, self.pattern.derivation, self.source.derivation, self.settings)

class P(GeoAlgorithm):
    pass

class SW(GeoAlgorithm):
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

