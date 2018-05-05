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

# Music21 User Settings
us = music21.environment.UserSettings()
us['directoryScratch'] = 'music_files/music21_temp_output'

query.insert(0, music21.chord.Chord(['G3', 'G4', 'B4', 'E5']))
query.insert(1, music21.chord.Chord(['F3', 'C4', 'C5', 'F5']))

module = lambda p: 'music_files/lupi/module_' + p + '.xml'
melody = lambda p: 'music_files/lupi/melody_' + p + '.xml'
palestrina_mass = lambda p: 'music_files/lupi/palestrina/Je_suis_desheritee_' + p + '.xml'
lupi_chanson = 'music_files/lupi/Je_suys_desheritee.xml'

modules_and_colours = [('A1', 'red'), ('A2', 'orange'), ('B1', 'blue'), ('schub_3', 'purple')]
module_melodies_and_colours = [
        ('A1_tenor', 'red'),
        ('A1_bass', 'red'),
        ('A2_tenor', 'orange'),
        ('A2_bass', 'orange'),
        ('B1_tenor', 'blue'),
        ('B1_bass', 'blue'),
        ('B2_soprano', 'purple'),
        ('B2_alto', 'purple'),
        ('B2_tenor', 'purple'),
        ('B2_bass', 'purple')]
melodies_and_colours = [
        ('P', 'orange'),
        ('Z', 'red'),
        ('X', 'purple'),
        ('Y', 'blue')]

palestrina_movements = ['Kyrie', 'Credo', 'Benedictus', 'Agnus_I', 'Agnus_II', 'Gloria', 'Sanctus']

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
                colour_occ(occ, c)

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
