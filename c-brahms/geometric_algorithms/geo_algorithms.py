from collections import namedtuple #for .scores immutable tuple
from pprint import pformat #for repr
from LineSegment import LineSegment
from NoteSegment import NotePointSet, K_entry, CmpItQueue, InterNoteVector, IntraNoteVector
from bisect import insort # to insert while maintaining a sorted list
from itertools import groupby # for K table initialization
from builtins import object #Python 2 and 3 next() compatibility
from more_itertools import peekable #for P class ptrs
from fractions import Fraction # for scale
import collections
import geometric_algorithms
import logging
import NoteSegment
import copy
import music21
import pdb

geo_algorithms_logger = logging.getLogger(__name__)

# @TODO measure total runtime with timeit (as a ratio of # of notes), store in an attribute like self.algorithmRunTime?
# @TODO implement 'threshold' == max
# @TODO implement threshold range, e.g. at least 15 matches but at least 1 mismatch, etc.

# @TODO maybe have separate user and algorithm settings. this would allow for translations like..
# mismatches?
# pattern_accuracy : 'all' --> threshold : len(pattern)
# pattern_accuracy : 'max' --> threshold = len(max(self.results, key=lambda x: len(x)))
DEFAULT_SETTINGS = {
        # Choose algorithm directly
        'algorithm' : 'P1',

        # Universal Algorithm settings
        'pattern_window' : 1,
        'source_window' : 5,
        'scale' : 'pure',
        'threshold' : 'all',
        'mismatches' : 0,
        'interval_func' : 'semitones',

        # P class settings
        #'segment' : False,
        #'overlap' : True,

        # More meaningful settings
        #'%pattern_window' : 1,
        #'%threshold' : 1,

        #Output
        'colour' : "red",
        'show_pattern' : True,
        }

class GeoAlgorithm(object):
    @classmethod
    def create(cls, pattern, source, **kwargs):

        # @TODO - do this here, or in algorithm init?
        # Maybe we shouldn't allow algorithm init outside of create()?
        self.process_settings(kwargs)

        if settings['scale'] == 1 or settings['scale'] == 'pure':
            cls = 'P'
        elif settings['scale'] == 'warped':
            cls = 'W'
        else:
            cls = 'S'

        if settings['threshold'] == 'all' and settings['mismatches'] == 0:
            tp = '1'
        else:
            tp = '2'

        if settings['algorithm']:
            algorithm_name = settings['algorithm']
        else:
            algorithm_name = cls + tp

        algorithm = getattr(geometric_algorithms, algorithm_name)
        return algorithm(pattern, source, **kwargs)

    """
    Generic base class to manage execution of P, S, and W algorithms
    """
    def __init__(self, pattern_input, source_input, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.logger.info('Creating a GeoAlgorithm instance')

        # @TODO parse scores first, then validate & translate in one step using
        # a subclassed dict object.

        # Defines self.pattern, self.patternPointSet, self.source, self.sourcePointSet
        self.parse_scores(pattern_input, source_input)

        # Defines self.user_settings and self.settings
        self.process_settings(kwargs)

        self.pre_process()

        # Run the algorithm, filter the occurrences, define an occurrence generator.
        #@TODO make occurrence objects for easier processing and testing
        self.results = (r for r in self.algorithm() if self.filter_result(r))
        self.occurrences = (self.process_result(r) for r in self.results)

        # Output them!
        self.output = (self.process_occurrence(occ) for occ in self.occurrences)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.output)

    def parse_scores(self, pattern_input, source_input):
        """
        Defines self.pattern, self.patternPointSet, self.source, and self.sourcePointSet
        Tests to see if the input is a file path or something else (possibly already parsed scores)

        Stores input file path in the derivation as a music21Object
        (each element in a derivation chain has to be a music21Object)

        Also runs all necessary pre-processing common to every algorithm
        (lexicographic sorting and chord flattening)
        """
        # @TODO what if the file is not found? It will fail!
        for input_type, inpt in (('pattern', pattern_input), ('source', source_input)):
            try:
                score = music21.converter.parse(inpt)
                score.derivation.origin = music21.ElementWrapper(inpt)
                score.derivation.method = 'music21.converter.parse()'
            except AttributeError:
                score = inpt
                try:
                    score.derivation.method = 'pre-parsed'
                except AttributeError:
                    raise ValueError("Invalid input: pattern and source must be music21"
                            + "streams or file names!")

            # Define self.pattern, self.source
            score.id = input_type
            setattr(self, input_type, score)

            # Define self.patternPointSet, self.sourcePointSet
            # NotePointSet sets the derivations of new streams on init
            point_set = NotePointSet(score)
            setattr(self, input_type + 'PointSet', point_set)

    def process_settings(self, user_settings):
        """
        Validates user-specified settings (AND validates the default settings)
        Translated keywords to algorithm-usable values
        e.g. 'threshold' = 'all' --> threshold = len(pattern)

        Some parameters are validated and translated before put into the settings dict
        These validation and translation functions are stored as attributes of self as _'key'
        They either return the value or raise a ValueError with the valid options
        """

        # Generate self.settings from the default settings
        self.settings = dict(DEFAULT_SETTINGS.items())
        self.user_settings = user_settings

        # Validate user KEYS
        for key in user_settings.keys():
            if key not in DEFAULT_SETTINGS.keys():
                raise ValueError("Parameter '{0}' is not a valid parameter.".format(key))

        # Validate and translate the setting arguments
        self.settings.update(user_settings)
        for key, arg in self.settings.items():
            try:
                # GET THE TRANSLATOR
                translator = getattr(self, '_' + key)
            except AttributeError:
                # If the parameter doesn't have a validator or translator, let it be
                continue
            try:
                # VALIDATE OR TRANSLATE THE DATA
                self.settings[key] = translator(arg)
            except ValueError as e:
                # Distinguish whether the invalid data came from the DEFAULT settings, 
                # or the user-specified ones
                if key in user_settings.keys():
                    message = "\n".join([
                    "Parameter '{0}' has an invalid value of {1}".format(key, arg),
                    "Valid arguments are: {0}".format(e.message)])
                else:
                    message = "\n".join([
                    "DEFAULT SETTINGS has set parameter '{0}' to an invalid value of {1}".format(key, arg),
                    "Valid arguments are: {0}".format(e.message)])
                raise ValueError(message)

        # @TODO make threshold and mismatches define an upper/lower bound range of tolerance
        if ('threshold' in user_settings) and ('mismatches' in user_settings):
            raise ValueError("Threshold and mismatches not yet both supported: use one or the other")

    def pre_process(self):
        pass

    def filter_result(self, result):
        """
        Decide whether the algorithm output is worth outputting
        """
        return True

    def process_result(self, result):
        """
        Given algorithm output, returns an occurrence
        """
        return result

    def process_occurrence(self, occ):
        """
        Given an occurrence, process it and produce output

        Implementation:
        We look at the original source and gather all of the notes which have been matched.
        First we tag these matched notes them with a group. We use groups rather than id's because
        music21 will soon implement group-based style functions.
        Next, we deepcopy the measure range excerpt in the score corresponding to matched notes
        Finally we untag the matched notes in the original score and output the excerpt
        """
        # @TODO colour pattern notes too
        # The notes in the score corresponding to this occurrence
        original_notes = [vec.noteEnd if not vec.noteEnd.derivation.origin
                else vec.noteEnd.derivation.origin for vec in occ]

        # Tag the matched notes
        for note in original_notes:
            note.groups.append('occurrence')

        # Get a copied excerpt of the score
        excerpt = copy.deepcopy(self.source.measures(
                numberStart = original_notes[0].getContextByClass('Measure').number,
                numberEnd = original_notes[-1].getContextByClass('Measure').number))

        # Untag the matched notes, process the occurrence
        for original_note, excerpt_note in zip(original_notes, excerpt.flat.getElementsByGroup('occurrence')):
            excerpt_note.color = 'red'
            original_note.groups.remove('occurrence')

        # Output the occurrence
        if self.settings['show_pattern']:
            output = music21.stream.Opus([self.pattern, excerpt, self.source])
        else:
            output = excerpt
        output.metadata = music21.metadata.Metadata()
        output.metadata.title = "Transposed by " + str(occ[0].y)

        #Save the pdf file as wtc-i-##_alg.pdf
        #temp_file = output.write('lily')
        # rename tmp.ly.pdf to file_name_base.pdf
        #os.rename(temp_file, ".".join(['output', 'pdf']))
        # rename tmp.ly to file_name_base.ly
        #os.rename(temp_file[:-4], ".".join(['output', 'ly']))

        return output

    def _algorithm(self, arg):
        valid_options = ['P1', 'P2', 'P3', 'S1', 'S2', 'W1', 'W2']
        if arg in valid_options:
            return getattr(geometric_algorithms, arg)
        else:
            raise ValueError(valid_options)

    def _threshold(self, arg):
        valid_options = []

        valid_options.append('all')
        if arg == 'all':
            return len(self.patternPointSet)

        valid_options.append('positive integer > 0')
        if isinstance(arg, int) and (arg > 0):
            return arg

        valid_options.append('max')
        if arg == 'max':
            raise ValueError("Threshold option 'max' not yet implemented")

        raise ValueError(valid_options)

    def _mismatches(self, arg):
        valid_options = []

        valid_options.append('positive integer >= 0')
        if isinstance(arg, int) and (arg >= 0):
            return arg

        raise ValueError(valid_options)

    def _scale(self, arg):
        valid_options = []

        valid_options.append('2-tuple of positive integers (numerator, denominator)')
        try:
            scale = Fraction(*arg)
        except (TypeError, ValueError):
            valid_options.append('integer or float >= 0')
            try:
                scale = Fraction(arg)
            except ValueError:
                pass

        valid_options.append('pure')
        if arg == 'pure': return 1
        valid_options.append('any', 'warped')
        if arg == 'any' or arg == 'warped': return arg

        if scale >= 0:
            return scale

        raise ValueError(valid_options)

    def _pattern_window(self, arg):
        valid_options = []

        valid_options.append('positive integer > 0')
        if isinstance(arg, int) and (arg > 0):
            return arg

        raise ValueError(valid_options)

    def _source_window(self, arg):
        return self._pattern_window(arg)

    def _interval_func(self, arg):
        valid_options = {
                'semitones' : lambda v: v.chromatic.semitones,
                'generic' : lambda v: v.generic.value,
                'base40' : lambda v: (
                    music21.musedata.base40.pitchToBase40(v.noteEnd) -
                    music21.musedata.base40.pitchToBase40(v.noteStart))}
        try:
            return valid_options[arg]
        except KeyError:
            raise ValueError(valid_options)

    def _colour(self, arg):
        # @TODO validate colour
        valid_options = ['any hexadecimal RGB colour?']
        return arg

    def __repr__(self):
        return "\n".join([
            self.__class__.__name__,
            "pattern = {0}".format(self.pattern.derivation),
            "source = {0}".format(self.source.derivation),
            "user settings = {0}".format(self.user_settings),
            "settings = {0}".format(self.settings)])

class P(GeoAlgorithm):
    """
    Implements algorithms P1, P2, and P3 from Ukkonen's 2003 papers

    P1, P2, and P3 all have separate algorithm implementations. They all use InterNoteVectors,
    which originate from each pattern note and iterate through the source.
    """
    def pre_process(self):
        super(P, self).pre_process()
        self.sourcePointSet_offsetSort = NotePointSet(self.source, offsetSort=True)

        interval_func = self.settings['interval_func']

        # Compute InterNoteVector generator pointers
        for note in self.patternPointSet:
            note.source_ptrs = [
                peekable((lambda p:
                    (InterNoteVector(p, self.patternPointSet, s, self.sourcePointSet,
                        interval_func, tp_type = 0)
                    for s in self.sourcePointSet))(note)),
                peekable((lambda p:
                    (InterNoteVector(p, self.patternPointSet, s, self.sourcePointSet,
                        interval_func, tp_type = 1)
                    for s in self.sourcePointSet))(note)),
                peekable((lambda p:
                    (InterNoteVector(p, self.patternPointSet, s, self.sourcePointSet_offsetSort,
                        interval_func, tp_type = 2)
                    for s in self.sourcePointSet))(note)),
                peekable((lambda p:
                    (InterNoteVector(p, self.patternPointSet, s, self.sourcePointSet_offsetSort,
                        interval_func, tp_type = 3)
                    for s in self.sourcePointSet))(note))]


class SW(GeoAlgorithm):
    """
    Implements algorithms S1, S2, W1, and W2 from Lemstrom's 2010 and 2011 papers

    These algorithms find "time-scaled" and "time-warped", "partial" occurrences
    of the pattern within the source. These four algorithms are so similar that
    they can be implemented identically in this one class.
    Algorithm SW finds every "time-warped" "partial" occurrence before being filtered by:
        1) the occurrence length (satisfying the "partial" vs. "exact" aspects of the
            original four algorithms)
        2) time-scaling (representing the S1, S2 algorithms from the 2010 paper)
    So the only difference between (S1, S2) and (W1, W2) is that the S algorithms
    override filter_result() to make sure it has a consistent time scaling. Otherwise
    they are identical and have the same runtime.

    Filters:
        'scale' : Only accepts occurrences of a particular scale
        'source_window' : Limits the search space by limiting the number
            of intervening notes allowed between any two source notes
            within the occurrence
            e.g. we do not want to match the first and last notes of the
                source and call that a sensible occurrence. Also, that would
                require an enormous search space depending on the score.
        'pattern_window' : Similar to 'source_window' but applies to the
            number of missing notes between any two matched pattern notes.

    Runtime
    It's shown in Lemstrom's paper that the runtime works out to:
        O(m * n * pattern_window * source_window * log(n))

    Summary of Implementation:
    Precompute all of the possible IntraNoteVectors in both the pattern and source.
    Then try to match them based on their vertical height (pitch difference)

    If an intra database vector and an intra pattern vector have the same height,
    then there is a horizontal shift which yields two matching pairs (the starting
    note of the intra pattern vector matches with the starting note of the intra
    database vector, and likewise with the ending note)
    So we pre_compute all those intra vector matches, and then form chains with them.

    Notes:
    Since ALL of the queues are initialized in pre_process, rather than
    just the first one (as in the pseudocode of S1), I think this algorithm
    will be able to find suffixes of perfect matches. But that's ok because
    we'll end up using Antti Laaksonen's faster version anyways.

    Since we yield every extension, the chain can be outputted as it is built.
    e.g. with a pattern of size 5 and a threshold of 4, we'll return all of the
    length-4 subsequences of the perfect match as well. (I think..)
    """


    def pre_process(self):
        """
        Initialize K tables

        Preprocessing:
            1) Precompute all possible intra database and intra pattern vectors.
            2) For each pattern note, keep:
                p.PQ:
                - a Priority Queue of antecedent chains, formed of intra database vectors.
                The queue is sorted lexicographically by the last vector's <ending note, starting note>
                This queue represents all possible chains which end at the current pattern note.

                p.K_table:
                - a Priority Queue of postcedents (one single intra database vector). The queue is
                sorted lexicographically by the database vector's <starting note, ending note>.
                This queue holds all the possible database vectors which can extend chains ending
                at the current pattern note.

                ** By using priority queues, we can process each of these antecedent and postcedent
                elements exactly once, and keep the run time down.
            3) Every intra vector match can constitute either the beginning of an antecedent chain,
            or a possible postcedent to an existing chain. So we push each one to the priority queues.
        """
        def compute_intra_vectors(point_set, window = 1):
            """
            Computes the set of IntraSetVectors in a NotePointSet.

            :int: window refers to the "reach" of any intra vector. It is the maximum
            number of intervening notes inbetween the start and end of an intra-vector.
            """
            # @TODO would be nice to use iterators instead of indices, couldn't get it to work
            point_set.intra_vectors = [IntraNoteVector(
                point_set[i], end, point_set, self.settings['interval_func'])
                    for i in range(len(point_set))
                    for end in point_set[i+1 : i+1+window]]

        # Define self.patternPointSet and self.sourcePointSet. Also processes settings
        super(SW, self).pre_process()

        # Compute Intra vectors
        compute_intra_vectors(self.patternPointSet, self.settings['pattern_window'])
        compute_intra_vectors(self.sourcePointSet, self.settings['source_window'])

        # Initialize antecedent and postcedent lists
        for p in self.patternPointSet:
            p.K_table = []
            p.PQ = {}

        self.sourcePointSet.intra_vectors.sort(key=lambda vec: vec.y)
        database_vectors = {key : list(g)
                for key, g in groupby(self.sourcePointSet.intra_vectors, lambda x: x.y)}

        for pattern_vec in self.patternPointSet.intra_vectors:
            for database_vec in database_vectors.get(pattern_vec.y, []):
                new_entry = K_entry(pattern_vec, database_vec)
                if new_entry.scale:
                    pattern_vec.noteStart.K_table.append(new_entry)
                    pattern_vec.noteEnd.PQ.setdefault(self.antecedentKey(new_entry), []).append(new_entry)

        # @TODO use bisect.insort() instead? or a priority queue?
        # We sort the K tables by <a, s, b> to keep them in a consistent order so that the
        # order of the algorithm output remains consistent
        # Also they have to at least be sorted by selfpostcedentKey(x) for the algorithm to work.
        for p in self.patternPointSet:
            p.K_table.sort(key=lambda x: self.postcedentKey(x) + (x.sourceVec.noteEndIndex,))

    def filter_result(self, result):
        return (# Results are intra-vectors, not notes, so we need one less
                ((result.w + 1) >= self.settings['threshold'])
                # Also filter with other non-algorithm specific user settings
                and super(SW, self).filter_result(result))

    def process_result(self, result):
        def extract_matching_pairs(K_entry, matching_pairs):
            """
            Tail recursively extracts the matching pairs from the final K_entry of an occurrence
            """
            if K_entry.y is None:
                return ([K_entry.matching_pairs.start]
                        + [K_entry.matching_pairs.end]
                        + matching_pairs)
            else:
                return extract_matching_pairs(K_entry.y, [K_entry.matching_pairs.end] + matching_pairs)

        return extract_matching_pairs(result, [])

    def algorithm(self):
        """
        Algorithm:
            1) Linesweep through the pattern[1:-1] (ignoring the first and last notes)
                - skipping the first note:
                    Recall that the antecedent chains and postcedents are intra database vectors.
                    They have a start and an end note. So we only to consider extending vectors
                    ending at the second note of the pattern, since this vector starts at the first.
                - skipping the last note:
                    similarly, the last note doesn't have any postcedents to extend chains with.
            2) For each postcedent associated with an intra pattern vector starting at this pattern
            note, look for antecedents to extend it with!
            3) When we find an antecedent to extend, we create a backlink with the K_entry constructor
            and then push it back into the appropriate PQ (the PQ of the pattern note at which this
            new antecedent chain ends)
            4) We return each new antecedent chain. filter_result will take user_settings into
            account and decide if it should be returned.
        """
        # Linesweep the pattern
        for p in self.patternPointSet[1:-1]:
            # Get groups of K_rows with identical binding keys
            for postcedentKey, postcedents in groupby(p.K_table, self.postcedentKey):
                ## For this binding key, get every combination of K_row and chain, then bind them.
                for K_row in postcedents:
                    # The antecedent chains we're looking for are hashed to the binding key
                    for antecedent in p.PQ.get(postcedentKey, []):
                        # BINDING OF EXTENSION
                        new_entry = K_entry(
                                K_row.patternVec, K_row.sourceVec, w = antecedent.w + 1, y = antecedent)
                        # Hash the end of this new source chain to its subsequent PQ
                        new_entry.patternVec.noteEnd.PQ.get(self.antecedentKey(K_row), []).append(new_entry)
                        yield new_entry

class S(SW):
    """
    Wrapper class for S-class algorithm.
    """
    def pre_process(self):
        # Antecedent and Postcedent Keys for S-class algorithms
        self.antecedentKey = lambda row: (row.sourceVec.noteEndIndex, row.scale)
        self.postcedentKey = lambda row: (row.sourceVec.noteStartIndex, row.scale)
        super(S, self).pre_process()


class W(SW):
    """
    Wrapper class for W-class algorithm.
    """
    def pre_process(self):
        # Antecedent and Postcedent Keys for W-class algorithms
        self.antecedentKey = lambda row: (row.sourceVec.noteEndIndex,) # pre_process uses tuple concatenation to sort K tables
        self.postcedentKey = lambda row: (row.sourceVec.noteStartIndex,)
        super(W, self).pre_process()
