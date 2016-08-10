from vis.analyzers.indexers import noterest, metre
import midiparser
import music21
import pandas

def shift_pattern(shift, pattern):
    """
    Used internally by class CBRAHMSTest
    Input:
        shift: 2-d vector (two-element list)
        pattern: 2-d vectors (list of two-element lists)
    Output: a new list of the vectors in 'pattern' translated by 'shift'
    """
    shifted_pattern = [list(a) for a in zip(map(lambda x: shift[0] + x, zip(*pattern)[0]), map(lambda y: shift[1] + y, zip(*pattern)[1]))]
    return shifted_pattern

def run_algorithm_with_midiparser(algorithm, pattern, source):
    q_score = music21.converter.parse(pattern)
    indexed_pattern = pandas.concat([
        noterest.NoteRestIndexer(q_score).run(),
        metre.DurationIndexer(q_score).run()], axis = 1).ffill()

    s_score = music21.converter.parse(source)
    indexed_source = pandas.concat([
        noterest.NoteRestIndexer(s_score).run(),
        metre.DurationIndexer(s_score).run(),
        metre.MeasureIndexer(s_score).run()], axis = 1).ffill()

    parsed_pattern = midiparser.run(indexed_pattern)
    parsed_source = midiparser.run(indexed_source)
    list_of_shifts = algorithm(parsed_pattern, parsed_source)
    return list_of_shifts
