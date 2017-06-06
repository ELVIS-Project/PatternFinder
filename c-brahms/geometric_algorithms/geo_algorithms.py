from collections import namedtuple #for .scores immutable tuple
from pprint import pformat #for repr and logging
from LineSegment import LineSegment
from NoteSegment import NotePointSet, K_entry, CmpItQueue, InterNoteVector, IntraNoteVector
from bisect import insort # to insert while maintaining a sorted list
from itertools import groupby # for K table initialization
from builtins import object #Python 2 and 3 next() compatibility
from more_itertools import peekable #for P class ptrs
from fractions import Fraction # for scale
import collections
import geometric_algorithms
import NoteSegment
import copy
import music21
import pdb
import logging
import yaml

class GeoAlgorithm(object):
    """
    A base class for P, S, and W algorithms

    Demands:
        pre_process -- unique pre processing for each algorithm or algorithm class
        filter_result -- decision making on whether an algorithm result should be outputted
                        based on user settings
        process_result -- since not all algorithm output is uniform, we need to process them
                        separately
        filtered_results -- generator which runs the algorithm and applies filter_result()
                            on its output
        occurrence_generator -- A.K.A. "processed_results". Runs through the filtered results
                                and applies process_result() to them
    """
    def __init__(self, pattern_input, source_input, settings):
        """
        An algorithm object parses the input and runs algorithm pre processing on __init__
        The object itself is a generator, so it won't begin looking for results until
        the user calls next(self)
        """
        # Log the creation of this object
        self.logger = logging.getLogger(__name__)
        self.logger.info('Creating a %s algorithm with:\n pattern %s\n source %s\n settings %s',
                self.__class__.__name__, pattern_input, source_input, pformat(settings))

        self.patternPointSet = pattern_input
        self.sourcePointSet = source_input
        self.settings = settings

        self.pre_process()

    def pre_process(self):
        pass

    def filter_result(self, result):
        return True

    def process_result(self, result):
        return result

    # @TODO ask Reiner if I should docstring an interfaced functions?
    def filtered_results(self):
        """
        A generator which filters the algorithm output based on self.filter_result
        This is the middle step in processing between algorithm output and occurrence output
        We implement this function in case someone wants to directly access algorithm filtered output
        """
        for r in self.algorithm():
            log_msg = "Algorithm yielded\n {0}...".format(pformat(r))
            if self.filter_result(r):
                log_msg += "\nPassed the filter!"
                self.logger.debug(log_msg)
                yield r
            else:
                log_msg += "\nDidn't pass the filter"
                self.logger.debug(log_msg)

    def occurrence_generator(self):
        """
        An occurrence generator: creates Occurrence objects from the filtered algorithm results.
        We implement this function so that users can look for occurrences again after having
        exhausted self.occurrences (without having to create another Algorithm object)
        """
        results = self.filtered_results()
        for r in results:
            occ = self.process_result(r)
            self.logger.info("Yielding occurrence %s", pformat(occ))
            yield occ

class P(GeoAlgorithm):
    """
    Implements algorithms P1, P2, and P3 from Ukkonen's 2003 papers

    P1, P2, and P3 all have separate algorithm implementations. They all use InterNoteVectors,
    which originate from each pattern note and iterate through the source.
    """

    def pre_process(self):
        super(P, self).pre_process()
        # @TODO come up with a better way to sort than this, srsly...
        self.sourcePointSet_offsetSort = NotePointSet(self.sourcePointSet, offsetSort=True)

        # Compute InterNoteVector generator pointers
        for note in self.patternPointSet:
            note.source_ptrs = [
                peekable((lambda p:
                    (InterNoteVector(p, self.patternPointSet, s, self.sourcePointSet,
                        self.settings['interval_func'], tp_type = 0)
                    for s in self.sourcePointSet))(note)),
                peekable((lambda p:
                    (InterNoteVector(p, self.patternPointSet, s, self.sourcePointSet,
                        self.settings['interval_func'], tp_type = 1)
                    for s in self.sourcePointSet))(note)),
                peekable((lambda p:
                    (InterNoteVector(p, self.patternPointSet, s, self.sourcePointSet_offsetSort,
                        self.settings['interval_func'], tp_type = 2)
                    for s in self.sourcePointSet))(note)),
                peekable((lambda p:
                    (InterNoteVector(p, self.patternPointSet, s, self.sourcePointSet_offsetSort,
                        self.settings['interval_func'], tp_type = 3)
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

        super(SW, self).pre_process()

        # Compute Intra vectors
        self.logger.info("Computing intra pattern vectors...")
        compute_intra_vectors(self.patternPointSet, self.settings['pattern_window'])
        self.logger.info("Computing intra source vectors...")
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

        # DEBUG LOG: a complete view of the K-tables
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug('K-table initialization: %s', pformat(
                list(enumerate(p.K_table for p in self.patternPointSet))))


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
