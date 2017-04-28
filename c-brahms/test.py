from geometric_algorithms import P1, P2, P3, S1, S2, W1, W2, DPW2
from pprint import pprint as pp
from collections import namedtuple
from parse_fugue_truth import parse_truth
import pickle
import os # to cycle tavern folders
import sys
import tests.tools
import music21
import LineSegment
import NoteSegment
import pdb

BACH_PATH = lambda x: os.path.join('music_files', 'bach_wtc1', 'wtc1f' + str(x).zfill(2) + '.krn')

class Solver(object):
    def __init__(self, pattern, source, settings):
        for alg in algorithms:
            pass
            #setattr(self, alg.__class__.__name__, alg(pattern, source, settings))

algorithms = [P1, P2, S1, S2, W1, W2, DPW2]

pscore = "music_files/" + "lemstrom2011_test/query_c.mid"
lemstrom_pattern = lambda x: 'music_files/lemstrom2011_test/query_' + x + '.mid'
lemstrom_source = "music_files/" + "lemstrom2011_test/leiermann.xml"

us = music21.environment.UserSettings()

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

pattern = BACH_PATH(1)
source = BACH_PATH(1)
settings = {}
#solver = {alg : obj for alg, obj in zip(algorithms, map(lambda x: x(pattern, source, settings), algorithms))}
#for pattern, source in ((lemstrom_pattern('a'), lemstrom_source)):
#    larry = namedtuple('solver', algorithms)
#    larry.P1(

