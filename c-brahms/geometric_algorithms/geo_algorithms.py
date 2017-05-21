from collections import namedtuple #for .scores immutable tuple
from pprint import pformat #for repr
from LineSegment import LineSegment
from NoteSegment import NotePointSet, K_entry, CmpItQueue, InterNoteVector
from bisect import insort # to insert while maintaining a sorted list
from itertools import groupby # for K table initialization
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
        self.settings = {key : val for key, val in DEFAULT_SETTINGS.items()}
        self.settings.update(settings)

        # Defines self.pattern and self.source
        # If file paths were given, they are stored in the stream derivations
        self.parse_scores(pattern_input, source_input)

        # Defines self.patternPointSet and self.sourcePointSet
        self.pre_process()

        # Run the algorithm, filter the occurrences, define an occurrence generator.
        #TODO make occurrence objects for easier processing and testing
        self.occurrences = (self.process_result(r) for r in self.algorithm() if self.filter_result(r))

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

        # TODO implement 'threshold' == max
        # TODO implement 'mismatch'?
        if self.settings['threshold'] == 'all':
            self.settings['threshold'] = len(self.patternPointSet)

    def process_result(self, r):
        return r

    def post_process(self):
        # Colour the score
        self.check = []
        if self.source.derivation.method == 'manual':
            return
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
        super(SW, self).pre_process()
        self.patternPointSet.compute_intra_vectors(self.settings['pattern_window'])
        self.sourcePointSet.compute_intra_vectors(self.settings['source_window'])

        for p in self.patternPointSet:
            # K table ordered by <a, b>
            p.K_table = CmpItQueue(lambda row: (
                row.noteStartIndex,
                row.noteEndIndex))

            # PQ ordered by <b, a>
            p.PQ = CmpItQueue(lambda row: (
                row.noteEndIndex,
                row.noteStartIndex))

        self.sourcePointSet.intra_vectors.sort(key=lambda vec: vec.y)
        database_vectors = {key : list(g)
                for key, g in groupby(self.sourcePointSet.intra_vectors, lambda x: x.y)}

        # NOTE actually i'm note sure about this. I think we can just have generators
        # and when the binding condition is satisfied, we extend it.
        #
        # we pre-initialize without generators because the algorithms sweepline across
        # the increasing intra_vectors, processing each element only once. otherwise,
        # if we generated them on the fly, we'd have to search through each K table for
        # antecedents to the binding.
        for pattern_vec in self.patternPointSet.intra_vectors:
            for database_vec in database_vectors[pattern_vec.y]:
                new_entry = K_entry(pattern_vec, database_vec)
                if new_entry.scale:
                    pattern_vec.noteStart.K_table.put(new_entry)
                    pattern_vec.noteEnd.PQ.put(new_entry)

    def filter_result(self, result):
        return ((result.w + 1) >= self.settings['threshold'])

    def process_result(self, result):
        def extract_matching_pairs(K_entry, matching_pairs):
            """
            Tail recursively extracts the matching pairs from the final K_entry of an occurrence
            """
            end_note = [InterNoteVector(K_entry.patternVec.noteEnd, self.patternPointSet,
                    K_entry.noteEnd, self.sourcePointSet)]
            if K_entry.y is None:
                return ([InterNoteVector(K_entry.patternVec.noteStart, self.patternPointSet,
                        K_entry.noteStart, self.sourcePointSet)]
                        + end_note
                        + matching_pairs)
            else:
                return extract_matching_pairs(K_entry.y, end_note + matching_pairs)

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
        for p in self.patternPointSet[1:-1]:
            for K_row in p.K_table:
                antecedent = lambda: p.PQ.queue[0].item.noteEndIndex
                binding = K_row.noteStartIndex

                # Use peek so that the first intra_vec to break this K_row can still be used for the next one
                while (p.PQ.qsize() > 0) and (antecedent() < binding):
                    p.PQ.next()

                # Modification to pseudocode: use "while" instead of "if" so that
                # you can chain many possible identical notes
                while (p.PQ.qsize() > 0) and (antecedent() == binding):
                    q = p.PQ.next()
                    new_entry = K_entry(K_row.patternVec, K_row, w = q.w + 1, y = q)
                    new_entry.patternVec.noteEnd.PQ.put(new_entry)
                    yield new_entry

class S(SW):

    def filter_result(self, result):
        return ((result.scale == result.y.scale)
                and (super(S, self).filter_result(result)))


class SWOld(GeoAlgorithm):

    """
    def pre_process(self):
        super(SW, self).pre_process()
        self.pattern.compute_intra_vectors(window = self.settings['pattern_window'])
        self.source.compute_intra_vectors(window = self.settings['source_window'])
        self.pattern.initialize_Ktables(self.source)
        #TODO if window == 0 or maybe "max"? set window to len(pattern)

        if isinstance(self.settings['mismatches'], (int, long)):
            ## TODO make it so you can't have threshold and mismatches set
            ## TODO make it so threshold refers to number of notes (add at +1 in alg)
            self.settings['threshold'] = len(self.pattern.flat.notes) - self.settings['mismatches'] - 1 #recall threshold refers to # of pattern vectors matched
        # If threshold has been passed in and intends to be 'max'..
        if self.settings['threshold'] == len(self.pattern.flat.notes):
            self.settings['threshold'] = self.settings['threshold'] - 1
    """

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

