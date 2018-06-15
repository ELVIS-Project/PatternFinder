import os
import music21
import logging
from pprint import pprint
from patternfinder import geometric_helsinki

tmp = 'music_files/music21_temp_output/tmp'
PALESTRINA_CORPUS = 'music_files/corpus/Palestrina/'

us = music21.environment.UserSettings()
us['directoryScratch'] = '/home/dgarfinkle/PatternFinder/music_files/music21_temp_output'

# Construct query
query = music21.stream.Score()
#query.insert(0, music21.chord.Chord(['C4', 'E4', 'A4', 'C5']))
#query.insert(1, music21.chord.Chord(['B-3', 'F4', 'B-4', 'D5']))
query.insert(0, music21.chord.Chord(['G3', 'G4', 'B4', 'E5']))
query.insert(1, music21.chord.Chord(['F3', 'C4', 'C5', 'F5']))


# Get mass file names (separate xml from midi)
mass_files = dict.fromkeys([mass_file for mass_file in os.listdir(PALESTRINA_CORPUS) if mass_file[-3:] == 'xml'], 0)

# Construct the finder!
#my_finder = geometric_helsinki.Finder(
#        pattern=query,
#        threshold = 0.90,
#        source_window = 3,
#        pattern_window = 4,
#        scale='warped',
#        interval_func = 'generic')

def run_1():
    for mass in mass_files.keys():
        print("Now processing " + mass)
        my_finder.update(source = PALESTRINA_CORPUS + mass)
        for occ in my_finder:
            for note in occ.source_notes:
                note.color = 'red'
            mass_files[mass] += 1
        #my_finder.source.write('lily.pdf', 'music_files/schubert_tasks/' + "_".join([str(mass_files[mass]), mass]))
        if mass_files[mass] > 0:
            output = my_finder.source.write('lily.png')
            os.rename(output,
                    'music_files/schubert_tasks_new/'
                    + "_".join([
                        't',
                        str(my_finder.settings['threshold'].algorithm),
                        str(mass_files[mass]),
                        mass])
                    + '.png')



def run_2():
    for mass in list(mass_files.keys())[:10]:
        print("Now processing " + mass)
        my_finder = geometric_helsinki.Finder(query, PALESTRINA_CORPUS + mass,
                threshold = 'all',
                scale = 'warped',
                interval_func = 'generic')
        return my_finder
        for occ in my_finder:
            for note in occ.notes:
                note.color = 'red'
            mass_files[mass] += 1
        #if mass_files[mass] > 0:
        #    output = my_finder.source.write('lily.png')
        #    os.rename(output,
        #            'music_files/schubert_tasks_new/'
        #            + "_".join([
        #                't',
        #                str(my_finder.settings['threshold'].algorithm),
        #                str(mass_files[mass]),
        #                mass])
        #            + '.png')
