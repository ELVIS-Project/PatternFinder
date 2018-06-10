import json
import subprocess
import music21
from patternfinder.geometric_helsinki.indexer import csv_notes
from app.dpwc import dpw_wrapper, gdb_dpw_wrapper, build_chains

us = music21.environment.UserSettings()
us['directoryScratch'] = '/home/dgarfinkle/PatternFinder/music_files/music21_temp_output/'

lemstrom_pattern = 'tests/data/lemstrom2011/query_a.mid'
lemstrom_target = 'tests/data/lemstrom2011/leiermann.xml'

def test_lemstrom():
    dpw_pattern_path = csv_notes(lemstrom_pattern)
    dpw_target_path = csv_notes(lemstrom_target)

    result_path = dpw_wrapper(dpw_pattern_path, dpw_target_path, 'tests/app/query_a.res')
    with open(result_path, 'r') as f:
        matrix = json.load(f)['matrix']

    print(build_chains(matrix, 2, 1, 14))

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
    test_identical()
    test_identical_twice()

    #gdb_lemstrom()

    test_lemstrom()
