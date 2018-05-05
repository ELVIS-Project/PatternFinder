import os
import music21
import patternfinder.geometric_helsinki

PALESTRINA_CORPUS = 'music_files/corpus/Palestrina/'

us = music21.environment.UserSettings()
us['directoryScratch']='/home/dgarfinkle/PatternFinder/music_files/music21_temp_output'

# Construct our query
query = music21.stream.Score()
#query.insert(0, music21.chord.Chord(['C4', 'E4', 'A4', 'C5']))
#query.insert(1, music21.chord.Chord(['B-3', 'F4', 'B-4', 'D5']))
query.insert(0, music21.chord.Chord(['G3', 'G4', 'B4', 'E5']))
query.insert(1, music21.chord.Chord(['F3', 'A4', 'C5', 'F5']))

#for mass_path in music21.corpus.getComposer('Palestrina'):
for mass_path in [mass_file for mass_file in os.listdir(PALESTRINA_CORPUS) if mass_file[-3:] == 'xml']:
    print("Processing " + mass_path)
    # Parse the mass
    mass_score = music21.converter.parse(os.path.join(PALESTRINA_CORPUS, mass_path))
    # Get an occurrence generator
    mass_finder = patternfinder.geometric_helsinki.Finder(query, mass_score,
            scale='warped',
            threshold='all',
            source_window=9)

    data = []
    # Colour all occurrences red
    for occurrence in mass_finder:
        occurrence.color_source_notes('red')
        data.append((occurrence.source_notes[0].getContextByClass('Measure').number, occurrence.source_notes[0].pitch.nameWithOctave))

    # Write the score if any notes have been coloured
    if any(n.style.color for n in mass_score.flat.notes):
        output = mass_score.write('lily.pdf')
        os.rename(output, os.path.join(
            'music_files/two_chord_data_2/',
            "_".join([
                'threshold' + str(mass_finder.settings['threshold'].user),
                'scale' + str(mass_finder.settings['scale'].user),
                os.path.basename(mass_path)[:-8]]
            + ["m{0}_pitch_{1}".format(measure, pitch) for measure, pitch in data]
            + ['.pdf'])))
