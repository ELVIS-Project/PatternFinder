import csv
import music21
from patternfinder.geometric_helsinki.geometric_notes import NotePointSet
from patternfinder.geometric_helsinki.finder import Finder

us = music21.environment.UserSettings()
us['directoryScratch'] = '/home/dgarfinkle/PatternFinder/music_files/music21_temp_output/'

def csv_notes(xml_input_path: str, dest: str = ''):
    stream = music21.converter.parse(xml_input_path)
    ps = NotePointSet(stream)

    if not dest:
        dest = xml_input_path + '.notes'

    with open(dest, 'w', newline='') as f:
        csv_writer = csv.writer(f, delimiter=',')
        csv_writer.writerow([len(ps.flat.notes)])
        for n in ps.flat.notes:
            csv_writer.writerow([n.offset, n.pitch.ps])

    return dest


def intra_vectors(xml_input_path: str, dest: str = '', window = 15):

    my_finder = Finder(music21.stream.Stream(), xml_input_path,
            threshold = 'all',
            pattern_window = 1,
            source_window = window,
            scale = 'warped')
            #interval_func = 'generic')

    notes = list(my_finder.sourcePointSet)
    vectors = my_finder.sourcePointSet.intra_vectors

    if not dest:
        dest = xml_input_path + '.vectors'

    with open(dest, 'w', newline='') as f:
        csv_writer = csv.writer(f, delimiter=',')
        csv_writer.writerow(['x', 'y', 'startIndex', 'endIndex', 'startPitch', 'endPitch', 'diatonicDiff', 'chromaticDiff'])
        csv_writer.writerow([len(notes)])
        csv_writer.writerow([len(vectors)])
        for v in vectors:
            csv_writer.writerow([v.x, v.y, v.noteStartIndex, v.noteEndIndex,
                                 v.noteStart.pitch.ps,
                                 v.noteEnd.pitch.ps,
                                 v.noteEnd.pitch.diatonicNoteNum - v.noteStart.pitch.diatonicNoteNum,
                                 int(v.noteEnd.pitch.ps - v.noteStart.pitch.ps)])

    return dest
