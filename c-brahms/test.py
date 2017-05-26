from geometric_algorithms import P1, P2, P3, S1, S2, W1, W2, DPW2, Finder
from pprint import pprint as pp
from collections import namedtuple
from parse_fugue_truth import parse_truth
from fractions import Fraction

# Testing CmpItQueue
from NoteSegment import CmpItQueue, IntraNoteVector, InterNoteVector, NotePointSet
from collections import namedtuple, Counter

import pickle
import os # to cycle tavern folders
import sys
import tests.tools
import music21
import NoteSegment
import pdb

### PATHS
# ex. TAVERN_PATH('B', 'B063', 1, 1) --> 'tavern/B/B063/Krn/B063_01_01_score.krn'
TAVERN_PATH = lambda composer, catalogue, variation, phrase: os.path.join('tavern', composer, catalogue, 'Krn', "_".join((catalogue, str(variation).zfill(2), str(phrase).zfill(2), 'score.krn')))
# ex. BACH_FUGUE_PATH(1) --> 'music_files/bach_wtc/wtc1f01.krn'
BACH_PATH = os.path.join('music_files', 'bach_wtc1')
BACH_FUGUE_PATH = lambda x: os.path.join(BACH_PATH, 'wtc1f' + str(x).zfill(2) + '.krn')
# ex. LEM_PATH_P('a') --> 'music_files/lemstrom2011_test/query_a.mid'
LEM_PATH_P = lambda x: 'music_files/lemstrom2011_test/query_' + x + '.mid'
LEM_PATH_S = os.path.join('music_files', 'lemstrom2011_test', 'leiermann.xml')

ALGORITHMS = [P1, P2, P3, S1, S2, W1, W2, DPW2]

# Music21 User Settings
us = music21.environment.UserSettings()

def tavern(composer, catalogue, variation, phrase):
    if composer == "Beethoven":
        c = 'B' # beethoven tag
    else:
        c = 'K' # mozart tag
    cat_num = c + str(catalogue).zfill(3)
    path = ('tavern', composer, cat_num, 'Krn', "_".join((cat_num, str(variation).zfill(2), str(phrase).zfill(2), 'score.krn')))
    return os.path.join(*path)


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

pattern = BACH_FUGUE_PATH(1)
source = BACH_FUGUE_PATH(1)
settings = {}

source = music21.stream.Stream()
pattern = music21.stream.Stream()

notes = [music21.note.Note(n) for n in ['G', 'B', 'D']]
source.repeatInsert(notes[0], [0 for i in range(1)])
source.insert([1, notes[1], 2, notes[2]])
pattern.insert([0, notes[0], 1, notes[1], 2, notes[2]])

# Music21 Objects
G = music21.note.Note('G')
B = music21.note.Note('B')
D = music21.note.Note('D')
Gmaj = music21.chord.Chord([G, B, D])

#Sorting test
sortPattern = music21.stream.Stream()
sortPattern.insert(0, G.transpose('M2'))
sortPattern.insert(0, G)
sortPattern.insert(1, B)
sortedPattern = NoteSegment.NotePointSet(sortPattern)

#Chord test
chordPattern = music21.stream.Stream()
chordPattern.insert([0, G, 1, Gmaj])
flatPattern = NoteSegment.NotePointSet(chordPattern)

# Testing CmpItQueue
customQueue = CmpItQueue(lambda x: x.y)
point = namedtuple('point', ['x', 'y'])
point1 = point(2, 3)
point2 = point(3, 4)

# Testing algorithms
lemP1 = P1(LEM_PATH_P('a'), LEM_PATH_S)
lemP2a = P2(LEM_PATH_P('a'), LEM_PATH_S)
lemP2b = P2(LEM_PATH_P('b'), LEM_PATH_S, **{'threshold' : 5})
lemP3a = P3(LEM_PATH_P('a'), LEM_PATH_S)
lemS1a = S1(LEM_PATH_P('a'), LEM_PATH_S)
lemS1b = S1(LEM_PATH_P('b'), LEM_PATH_S, **{'pattern_window' : 5, 'threshold' : 5})
lemS1c = S1(LEM_PATH_P('c'), LEM_PATH_S)
lemS1d = S1(LEM_PATH_P('d'), LEM_PATH_S, **{'pattern_window' : 5, 'threshold' : 5})
lemW2a = W2(LEM_PATH_P('a'), LEM_PATH_S)

"""
P3, S1, these are doing some weird things, like finding different matches after many trials.  results = {}
for i in range(100):
    lemP3a = P3(LEM_PATH_P('a'), LEM_PATH_S)
    for o in lemP3a.occurrences:
        foo = tuple(vec for vec in o)
        counter.update(foo)
        print(i)

"""



import SimpleHTTPServer
import SocketServer

PORT = 8000

#Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
#httpd = SocketServer.TCPServer(("", PORT), Handler)

print("ready to serve at port use 'httpd.serve_forever()'" + str(PORT))

