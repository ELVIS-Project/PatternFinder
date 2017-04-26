from geometric_algorithms import P1, P2, S1, S2, W1, W2, DPW2
from pprint import pprint as pp
from collections import namedtuple
from parse_fugue_truth import parse_truth
import math #to round the measure ranges to nearest int
import pickle
import os # to cycle tavern folders
import sys
import tests.tools
import music21
import LineSegment
import NoteSegment
import pdb

# PATHS
BACH_PATH = lambda x: os.path.join('music_files', 'bach_wtc1', 'wtc1f' + str(x).zfill(2) + '.krn')
LEM_PATH_P = lambda x: 'music_files/lemstrom2011_test/query_' + x + '.mid'
LEM_PATH_S = os.path.join('music_files', 'lemstrom2011_test', 'leiermann.xml')

ALGORITHMS = [P1, P2, S1, S2, W1, W2, DPW2]

# Music21 User Settings
us = music21.environment.UserSettings()

# To get a voice from ground truth and return the part index in the kern score
voice_to_part = lambda part: {p : n for n, p in enumerate(['S', 'A', 'T', 'B'])}[part.upper()]

class Solver(object):
    def __init__(self, pattern, source, settings):
        for alg in algorithms:
            pass
            #setattr(self, alg.__class__.__name__, alg(pattern, source, settings))


be = 'Beethoven'
mo = 'Mozart'
def tavern(composer, catalogue, variation, phrase):
    if composer == "Beethoven":
        c = 'B' # beethoven tag
    else:
        c = 'K' # mozart tag
    cat_num = c + str(catalogue).zfill(3)
    path = ('tavern', composer, cat_num, 'Krn', "_".join((cat_num, str(variation).zfill(2), str(phrase).zfill(2), 'score.krn')))
    return os.path.join(*path)

for (dirpath, dirnames, filenames) in os.walk('tavern'):
    if os.path.basename(dirpath) == 'Krn':
        pass


# variation indexes from 0, phrase indexes from 1 
#rachel = S1(tavern(be, 63, 0, 1), tavern(be, 63, 1, 1))

"""
lorry = P1(lemstrom_pattern('a'), lemstrom_source)
kat = P2(lemstrom_pattern('b'), lemstrom_source)
ralph = S1(lemstrom_pattern('c'), lemstrom_source)
joseph = S2(lemstrom_pattern('d'), lemstrom_source)
carlos = W1(lemstrom_pattern('e'), lemstrom_source)
justin = W2(lemstrom_pattern('f'), lemstrom_source)
john = DPW2(lemstrom_pattern('f'), lemstrom_source)
"""

f = open('fugue_truth.pckl', 'rb')
bach_truth = pickle.load(f)
f.close()

### Loop through fugues
pattern = music21.converter.parse(BACH_PATH(1))
source = music21.converter.parse(BACH_PATH(1))
settings = {'parsed_input' : True}

### Find each subject
first_occ = min(bach_truth['wtc-i-01']['S']['occurrences'], key=lambda x: x['measure'])

# TODO get the offset of the beginning and end of the subject, then get the notes.
lower = int(math.floor(first_occ['measure']))
upper = int(math.ceil(first_occ['measure'] + first_occ['length']))
pattern = pattern.parts[voice_to_part(first_occ['voice'])].measures(lower, upper)


