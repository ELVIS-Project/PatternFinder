from pprint import pprint as pp
from collections import namedtuple
from fractions import Fraction

# Testing CmpItQueue
from geometric_helsinki.finder import Finder
from geometric_helsinki.NoteSegment import CmpItQueue, IntraNoteVector, InterNoteVector, NotePointSet
from collections import namedtuple, Counter

import logging
import os
import music21
import pdb

### PATHS
# ex. TAVERN_PATH('B', 'B063', 1, 1) --> 'tavern/B/B063/Krn/B063_01_01_score.krn'
TAVERN_PATH = lambda composer, catalogue, variation, phrase: os.path.join('tavern', composer, catalogue, 'Krn', "_".join((catalogue, str(variation).zfill(2), str(phrase).zfill(2), 'score.krn')))

# ex. BACH_FUGUE_PATH(1) --> 'music_files/bach_wtc/wtc1f01.krn'
BACH_PATH = os.path.join('music_files', 'bach_wtc1')
BACH_FUGUE_PATH = lambda x: os.path.join(BACH_PATH, 'wtc1f' + str(x).zfill(2) + '.krn')
SUBJECT_PATH = lambda f, s: os.path.join(BACH_PATH, 'e_wtc1f' + str(f).zfill(2) + '_' + s + '.xml')

# ex. LEM_PATH_P('a') --> 'music_files/lemstrom2011_test/query_a.mid'
LEM_PATH_P = lambda x: 'music_files/lemstrom2011_test/query_' + x + '.mid'
LEM_PATH_S = os.path.join('music_files', 'lemstrom2011_test', 'leiermann.xml')

# Music21 User Settings
us = music21.environment.UserSettings()
us['directoryScratch'] = 'music_files/music21_temp_output'

#LOGGING
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
logger.addHandler(ch)

def tavern(composer, catalogue, variation, phrase):
    if composer == "Beethoven":
        c = 'B' # beethoven tag
    else:
        c = 'K' # mozart tag
    cat_num = c + str(catalogue).zfill(3)
    path = ('tavern', composer, cat_num, 'Krn', "_".join((cat_num, str(variation).zfill(2), str(phrase).zfill(2), 'score.krn')))
    return os.path.join(*path)


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
sortedPattern = NotePointSet(sortPattern)

#Chord test
chordPattern = music21.stream.Stream()
chordPattern.insert([0, G, 1, Gmaj])
flatPattern = NotePointSet(chordPattern)

# Testing CmpItQueue
customQueue = CmpItQueue(lambda x: x.y)
point = namedtuple('point', ['x', 'y'])
point1 = point(2, 3)
point2 = point(3, 4)

# Testing algorithms
"""
lemP1 = Finder(LEM_PATH_P('a'), LEM_PATH_S, auto_select=False, algorithm='P1')
lemP2a = Finder(LEM_PATH_P('a'), LEM_PATH_S, auto_select=False, algorithm='P2')
lemP2b = Finder(LEM_PATH_P('b'), LEM_PATH_S, auto_select=False, algorithm='P2')
lemS1a = Finder(LEM_PATH_P('a'), LEM_PATH_S, auto_select=False, algorithm='S1')
"""

"""
P3, S1, these are doing some weird things, like finding different matches after many trials.  results = {}
for i in range(100):
    lemP3a = P3(LEM_PATH_P('a'), LEM_PATH_S)
    for o in lemP3a.occurrences:
        foo = tuple(vec for vec in o)
        counter.update(foo)
        print(i)

"""

# @TODO shouldn't get "manually preparsed" for the source here
# @TODO setting "auto_select" and "interval_func" in Finder __init__ doesn't work. Only works on update()

# Test P1 generic intervals fugue 2
#bach2 = Finder(SUBJECT_PATH(2, 'S'), BACH_FUGUE_PATH(2))
#bach2.update(pattern=bach2.patternPointSet[:-2], auto_select=False, interval_func='generic')

#@TODO it's a little funky if you do source first then update with pattern. should be able to. but the source derivation gets lost, and a Lilypond exception comes up & you can't write the score...
from more_itertools import consume
module = lambda p: 'music_files/lupi/module_' + p + '.xml'
melody = lambda p: 'music_files/lupi/melody_' + p + '.xml'
palestrina_mass = lambda p: 'music_files/lupi/palestrina/Je_suis_desheritee_' + p + '.xml'
lupi_chanson = 'music_files/lupi/Je_suys_desheritee.xml'

modules_and_colours = [('A1', 'red'), ('A2', 'orange'), ('B1', 'blue'), ('schub_3', 'purple')]
melodies_and_colours = [
        ('P', 'orange'),
        ('Z', 'red'),
        ('X', 'purple'),
        ('Y', 'blue')]

palestrina_movements = ['Kyrie', 'Credo', 'Benedictus', 'Agnus_I', 'Agnus_II', 'Gloria', 'Sanctus']

def find_lupi_modules():
    lupi = Finder(source=lupi_chanson)
    for m, c in modules_and_colours:
        lupi.update(pattern=module(m), threshold='all', colour=c)
        consume(lupi)
    return lupi

def colour_occ(occ, colour):
    source_notes = [vec.noteEnd if vec.noteEnd.derivation.origin is None
            else vec.noteEnd.derivation.origin for vec in occ]

    # Colour the source notes
    for note in get_source_notes_from_occ(occ):
        note.color = c

def get_source_notes_from_occ(occ):
    # get the note, or get the chord that the note came from
    return [vec.noteEnd if vec.noteEnd.derivation.origin is None
            else vec.noteEnd.derivation.origin for vec in occ]

def find_palestrina(dest='find_modules', masses=palestrina_movements, modules=modules_and_colours,
        threshold=0.70, scale='warped', source_window=5, pattern_window=3, interval_func='semitones'):
    palestrina = Finder()
    results = {mass : [] for mass in masses}
    for mass in masses:
        palestrina.update(source=palestrina_mass(mass))
        for m, c in modules:
            counter = 0
            palestrina.update(pattern=melody(m), threshold=threshold, scale=scale,
                    colour=c, source_window=source_window, pattern_window=pattern_window, interval_func=interval_func)

            for occ in palestrina:
                counter += 1

            results[mass].append((m, counter, c))

        # Write the coloured score
        file_name = 'music_files/lupi/' + dest + '/' + "_".join([
            "t{0:.0f}%".format(threshold * 100),
            'p' + str(palestrina.settings['pattern_window']),
            's' + str(palestrina.settings['source_window']),
            'i' + interval_func,
            mass])
        temp_file = palestrina.sourcePointSet.derivation.origin.write('lily.pdf')
        os.rename(temp_file, ".".join([file_name, 'pdf']))
    return results

def find_generic_semitone_difference(dest='find_modules', masses=palestrina_movements, modules=modules_and_colours, threshold=0.70, scale='warped', source_window=5, pattern_window=3, interval_func='semitones'):
    palestrina = Finder()
    results = {mass : [] for mass in masses}
    for mass in masses:
        palestrina.update(source=palestrina_mass(mass))
        for m, c in modules:
            counter = 0

            #Tag all the notes found with interval_func = semitones
            palestrina.update(pattern=melody(m), threshold=threshold, scale=scale, colour=c, source_window=source_window, pattern_window=pattern_window, interval_func='semitones')
            for occ in palestrina:
                for note in get_source_notes_from_occ(occ):
                    note.groups.append('semitones')

            # Colour all the notes found by the generic finder and note found by the semitone finder 
            palestrina.update('generic')
            for occ in palestrina:
                for note in get_source_notes_from_occ(occ):
                    if 'semitones' not in note.groups:
                        note.color = c

        file_name = 'music_files/lupi/' + dest + '/' + "_".join([
            "t{0:.0f}%".format(threshold * 100),
            'p' + str(palestrina.settings['pattern_window']),
            's' + str(palestrina.settings['source_window']),
            'i' + 'difference',
            mass])
        temp_file = palestrina.sourcePointSet.derivation.origin.write('lily.pdf')
        os.rename(temp_file, ".".join([file_name, 'pdf']))

#foo = find_palestrina(dest='find_melodies', threshold=0.9, source_window=3, pattern_window=2, scale='warped', modules=melodies_and_colours, interval_func='semitones')
#bar = find_palestrina(dest='find_melodies', threshold=0.9, source_window=3, pattern_window=2, scale='warped', modules=melodies_and_colours, interval_func='generic')

#find_generic_semitone_difference(dest='find_melodies', threshold=0.9, source_window=3, pattern_window=2, scale='warped', modules=melodies_and_colours, interval_func='semitones')

#palestrina.update(scale='warped', mismatches=6, pattern_window=3)
#lassus = Finder('music_files/lupi/module_A2.xml', 'music_files/lupi/Missa-Je-suis-desheritee-Lassus_Kyrie.xml')
#lassus.update(scale='warped', mismatches=6, pattern_window=3)

#lassus_full = Finder('music_files/lupi/module_A2.xml', 'music_files/lupi/OMR_Missa_Je_suys_desheritee_Lassus.xml')

#lupi = Finder('music_files/lupi/module_A2.xml', 'music_files/lupi/Je_suys_desheritee.xml')
