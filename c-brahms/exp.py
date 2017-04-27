from geometric_algorithms import P1, P2, S1, S2, W1, W2, DPW2, geoAlgorithm
from pprint import pprint as pp
from collections import namedtuple
from parse_fugue_truth import parse_truth
from fractions import Fraction
from LineSegment import * #for pickling
import pandas as pd #for data wrangling
import logging # to keep track of errors and progress
import NoteSegment #for pickling
import math #to round the measure ranges to nearest int
import pickle
import os # to cycle tavern folders
import sys
import tests.tools
import music21
import LineSegment
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

ALGORITHMS = [P1, P2, S1, S2, W1, W2, DPW2]

FILTER_FOR_SUBJECT_LABELS = lambda x: [x for x in x if x in ['S', 'S2', 'CS', 'CS2', 'Saug', 'Sinv']]

SUBJECT_COLOUR = {
        'S' : 'blue',
        'S2' : 'cyan',
        'CS' : 'red',
        'CS2' : 'orange',
        'Saug' : 'purple',
        'Sinv' : 'pink'
        }

# Music21 User Settings
us = music21.environment.UserSettings()

# To get a voice from ground truth and return the part index in the kern score
voice_to_part = lambda part: {p : n for n, p in enumerate(['S', 'A', 'T', 'B', 'C'])}[part.upper()]

def get_pattern_from_fugue(shelf, fugue_tag, subject):
    score = music21.converter.parse(BACH_FUGUE_PATH(fugue_tag[-2:]))

    #TEMP FIX get the sorted, parsed NoteSegment representation of the score
    #sorted_source_notes = 

    # Find first occurrence of this subject
    first_occ = min(shelf[fugue_tag][subject]['occurrences'], key=lambda x: x['measure'])

    # Get the offset range of this first statement
    measure_number, measure_loc, part_index = (int(first_occ['measure']), first_occ['measure'] - int(first_occ['measure']), voice_to_part(first_occ['voice']))
    measure = score.parts[part_index].measure(measure_number)

    # 'start' and 'end' are quarterLength offset modifications
    start_offset = (measure.duration.quarterLength * measure_loc) + first_occ['start']
    end_offset = start_offset + (measure.duration.quarterLength * first_occ['length']) + first_occ['end']

    ## filter the pattern based on this range
    lower = int(math.floor(first_occ['measure']))
    upper = int(math.ceil(first_occ['measure'] + first_occ['length']))
    # fugue #20 has a weird extra spline; filter it out with [1:]
    if fugue_tag == "wtc-i-20":
        pattern = score.measures(lower, upper)[1:].parts[part_index]
    else:
        pattern = score.measures(lower, upper).parts[part_index]

    for elt in pattern.recurse(classFilter=('GeneralNote')):
        elt_offset_in_hierarchy = elt.getOffsetBySite(pattern.flat)
        if elt_offset_in_hierarchy < start_offset or elt_offset_in_hierarchy >= end_offset:
            pattern.remove(elt, recurse=True)

    return pattern

# TODO so you can compare occurrences with the shift ouput from algorithms
def get_offset_from_label(shelf, fugue_tag, label):
    score = music21.parse.converter(shelf[fugue_tag]['file'])

    measure_number = shelf[fugue_tag][label]['measure']
    # Get the offset range of this label
    measure_number, measure_loc, part_index = (measure_number, measure_number - int(measure_number), voice_to_part(first_occ['voice']))
    measure = score.parts[part_index].measure(measure_number)

    # 'start' and 'end' are quarterLength offset modifications
    start_offset = (measure.duration.quarterLength * measure_loc) + first_occ['start']
    end_offset = start_offset + (measure.duration.quarterLength * first_occ['length']) + first_occ['end']

    ## filter the pattern based on this range
    lower = int(math.floor(first_occ['measure']))
    upper = int(math.ceil(first_occ['measure'] + first_occ['length']))
    # fugue #20 has a weird extra spline; filter it out with [1:]
    if fugue_tag == "wtc-i-20":
        pattern = score.measures(lower, upper)[1:].parts[part_index]
    else:
        pattern = score.measures(lower, upper).parts[part_index]

    for elt in pattern.recurse(classFilter=('GeneralNote')):
        elt_offset_in_hierarchy = elt.getOffsetBySite(pattern.flat)
        if elt_offset_in_hierarchy < start_offset or elt_offset_in_hierarchy >= end_offset:
            pattern.remove(elt, recurse=True)
    pass


def write_score(score, file_name_base):

    # Save the pdf file as wtc-i-##_alg.pdf
    temp_file = score.write('lily.pdf')
    # rename tmp.ly.pdf to file_name_base.pdf
    os.rename(temp_file, ".".join([file_name_base, '.pdf']))
    # rename tmp.ly to file_name_base.ly
    os.rename(temp_file[:-4], ".".join([file_name_base, '.ly']))

    # Save the xml file as wtc-i-##_alg.xml
    #temp_file = score.write('xml')
    #os.rename(temp_file, ".".join([file_name_base, '.xml']))


def run2(fugue_indices = range(1,24), algorithms = [P1, P2, S1, S2, W1, W2], settings = {}):
    df_occ_index = []

    ## LOOP THROUGH ALGORITHMS ##
    for algorithm in algorithms:
        for i in fugue_indices:
            fugue_tag = 'wtc-i-' + str(i).zfill(2)

            source = music21.converter.parse(BACH_FUGUE_PATH(i))
            settings.update({'parsed_input' : True, 'runOnInit' : False})

            ## LOOP THROUGH SUBJECTS ##
            for subject in FILTER_FOR_SUBJECT_LABELS(bach_truth[fugue_tag].keys()):
                print("Fetching pattern " + subject + " from fugue " + fugue_tag)
                pattern = get_pattern_from_fugue(bach_truth, fugue_tag, subject)

                if len(pattern.flat.notes) == 0:
                    print("Pattern has no length.")
                    logging.warning("Pattern has no length")
                    logging.debug("start_offset {0}, end_offset{1}".format(start_offset, end_offset))
                    continue

                ## PREPARE DATAFRAME INDICES
                # list occurrences:
                #bach_truth[fugue_tag(i)][subject]['occurrences'] for subject in FILTER_FOR_SUBJECT_LABELS(bach_truth[fugue_tag(i)].keys()) for i in range(1,25)]
                df_occ_index.append(map(lambda x: (fugue_tag, subject, x['measure']), bach_truth[fugue_tag][subject]['occurrences']))
                df_columns = [x.__name__ for x in algorithms]




                ## RUN THE ALGORITHM ##
                print("Creating algorithm object " + algorithm.__name__)
                larry = algorithm(pattern, source, settings)
                larry.settings.update({'colour' : SUBJECT_COLOUR[subject]})
                print("Running algorithm " + larry.__class__.__name__ + " on fugue " + fugue_tag + " subject " + subject)
                try:
                    larry.run()
                except:
                    logging.error("Algorithm Failed on fugue {0}, subject {1} \n".format(fugue_tag, subject) + str(larry))
                    continue

            ## WRITE THE SCORE ##
            new_file_base = os.path.join(BACH_PATH, "_".join([fugue_tag, larry.__class__.__name__, "all"])) # with all subjects coloured at once
            write_score(larry.original_source, new_file_base)

            return pd.DataFrame(0, reduce(lambda x, y: x+y, df_occ_index), df_columns)



logging.basicConfig(filename='exp.log', level=logging.DEBUG)

f = open('fugue_truth.pckl', 'rb')
bach_truth = pickle.load(f)
f.close()



### TAVERN
for (dirpath, dirnames, filenames) in os.walk('tavern'):
    if os.path.basename(dirpath) == 'Krn':
        pass

