import json
import subprocess
import music21
from patternfinder.geometric_helsinki.indexer import csv_notes, intra_vectors
from app.dpwc import dpw_wrapper, gdb_dpw_wrapper, w_wrapper, wcpp_wrapper, build_chains, get_occurrences_from_matrix

us = music21.environment.UserSettings()
us['directoryScratch'] = '/home/dgarfinkle/PatternFinder/music_files/music21_temp_output/'

lemstrom_pattern = 'tests/data/lemstrom2011/query_a.mid'
lemstrom_target = 'tests/data/lemstrom2011/leiermann.xml'

def test_wcpp(pattern, target):
    #w_pattern_path = intra_vectors(pattern, window = 1)
    w_pattern_path = pattern + '.vectors'
    #w_target_path = intra_vectors(target, window = 8)
    w_target_path = target + '.vectors'
    result_path = 'tests/app/query_a.res'

    result_path = wcpp_wrapper(w_pattern_path, w_target_path, result_path)
    with open(result_path, 'r') as f:
        result = f.read()

    print(result)

def test_w(pattern, target):
    #w_pattern_path = intra_vectors(pattern, window = 1)
    w_pattern_path = pattern + '.vectors'
    #w_target_path = intra_vectors(target)
    w_target_path = target + '.vectors'
    result_path = 'tests/app/query_a.res'

    result_path = w_wrapper(w_pattern_path, w_target_path, result_path)
    with open(result_path, 'r') as f:
        result = f.read()

    print(result)

def gdb_lemstrom():
    dpw_pattern_path = csv_notes(lemstrom_pattern)
    dpw_target_path = csv_notes(lemstrom_target)

    gdb_dpw_wrapper(dpw_pattern_path, dpw_target_path, 'tests/app/query_a.res')

def test_identical():
    stream = music21.converter.parse('tinynotation: c4 e4 g4')
    pattern = stream.write('xml', 'tests/app/identical_pattern.xml')
    target = stream.write('xml', 'tests/app/identical_target.xml')

    dpw_pattern_path = csv_notes(pattern)
    dpw_target_path = csv_notes(target)

    result_path = dpw_wrapper(dpw_pattern_path, dpw_target_path, 'tests/app/identical.res')

    with open(result_path, 'r') as f:
        matrix = json.load(f)['matrix']

    assert build_chains(matrix, 1, 1, 1) == [0, 1, 2]

def test_identical_twice():
    pattern_stream = music21.converter.parse('tinynotation: c4 e4 g4')
    pattern = pattern_stream.write('xml', 'tests/app/identical_twice_pattern.xml')
    target_stream = music21.converter.parse('tinynotation: c4 e4 g4 c4 e4 g4')
    target = target_stream.write('xml', 'tests/app/identical_twice_target.xml')

    dpw_pattern_path = csv_notes(pattern)
    dpw_target_path = csv_notes(target)

    result_path = dpw_wrapper(dpw_pattern_path, dpw_target_path, 'tests/app/identical_twice.res')

    with open(result_path, 'r') as f:
        matrix = json.load(f)['matrix']

    assert build_chains(matrix, 1, 1, 1) == [0, 1, 2]
    assert build_chains(matrix, 1, 1, 4) == [3, 4, 5]


if __name__ == '__main__':
    #test_identical()
    #est_identical_twice()

    #gdb_lemstrom()

    test_w(lemstrom_pattern, lemstrom_target)
    #test_wcpp(lemstrom_pattern, lemstrom_target)
