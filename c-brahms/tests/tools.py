from vis.analyzers.indexers import noterest, metre
import midiparser
import music21
import pandas
import pdb

def shift_pattern(shift, pattern):
    """
    Used internally by class CBRAHMSTest
    Input:
        shift: list of size n
        pattern: list of lists, all of size n
    Output: a new list of the vectors in 'pattern' translated by 'shift'
    """
    shifted_pattern = map(lambda elt: map(sum, zip(elt, shift)), pattern)
    return shifted_pattern

"""
def num_mismatches(pattern, source, shift):
    # Sort the lists
    pdb.set_trace()
    pattern.sort()
    source.sort()
    # Shift the pattern
    shifted_pattern = shift_pattern(shift, pattern)


    # Consider all starting locations for comparison (possible duplicates)
    source_starts = [i for i, j in enumerate(source) if j == shifted_pattern[0]]
    mismatches = [len(filter(lambda x: x[0] != x[1], zip(shifted_pattern, source[st:len(pattern)]))) for st in source_starts]

    if mismatches == []:
        return 0
    else:
        return min(mismatches)
"""

def index_source_from_score(source):
    s_score = music21.converter.parse(source)
    return pandas.concat([
        noterest.NoteRestIndexer(s_score).run(),
        metre.DurationIndexer(s_score).run(),
        metre.MeasureIndexer(s_score).run()], axis = 1)

def index_pattern_from_score(pattern):
    q_score = music21.converter.parse(pattern)
    return pandas.concat([
        noterest.NoteRestIndexer(q_score).run(),
        metre.DurationIndexer(q_score).run()], axis = 1)

def run_algorithm_with_indexed_pieces(algorithm, indexed_pattern, indexed_source):
    parsed_pattern = midiparser.run(indexed_pattern)
    parsed_source = midiparser.run(indexed_source)
    return algorithm(parsed_pattern, parsed_source)

def run_algorithm_with_midiparser(algorithm, pattern, source):
    parsed_pattern = midiparser.run(index_pattern_from_score(pattern))
    parsed_source = midiparser.run(index_source_from_score(source))
    return algorithm(parsed_pattern, parsed_source)
