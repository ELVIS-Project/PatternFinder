from geometric_algorithms import P1, P2, P3, S1, S2, W1, W2
from pprint import pprint as pp
from collections import namedtuple
from parse_fugue_truth import parse_truth
from fractions import Fraction
from LineSegment import * #for pickling
from functools import partial
import pandas as pd #for data wrangling
import logging # to keep track of errors and progress
import NoteSegment #for pickling
import math #to round the measure ranges to nearest int
import pickle
import os # to cycle tavern folders
import sys
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

ALGORITHMS = [P1, P2, P3, S1, S2, W1, W2]

FILTER_FOR_SUBJECT_LABELS = lambda x: [x for x in x if x in ['S', 'S2', 'CS', 'CS2', 'Saug', 'Sinv']]

COLOUR_SCHEMA = {
        'S' : 'blue',
        'S2' : 'cyan',
        'CS' : 'red',
        'CS2' : 'orange',
        'Saug' : 'purple',
        'Sinv' : 'pink'
        }

DF_COLUMNS = [
        'gt',
        'occ',
        'fug',
        'sub',
        'alg',
        'pw',
        '%pw',
        'sw',
        'thresh',
        '%thresh',
        'sub_len']

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
    # #TODO you're lucky: the first occurrence always happens to be SATBC, but what about 'SA' or '*'?
    measure_number, measure_loc, part_index = (int(first_occ['measure']), first_occ['measure'] - int(first_occ['measure']), voice_to_part(first_occ['voice']))
    measure = score.parts[part_index].measure(measure_number)

    # 'start' and 'end' are quarterLength offset modifications
    start_offset = (measure.duration.quarterLength * measure_loc) + first_occ['start']
    end_offset = start_offset + (measure.duration.quarterLength * first_occ['length']) + first_occ['end']

    ## filter the pattern based on this range
    lower = int(math.floor(first_occ['measure']))
    upper = int(math.ceil(first_occ['measure'] + first_occ['length']))
    # fugue #20 has a weird extra spine; filter it out with [1:]
    if fugue_tag == "wtc-i-20":
        pattern = score.measures(lower, upper)[1:].parts[part_index]
    else:
        pattern = score.measures(lower, upper).parts[part_index]

    # TODO TEMP fix pattern must have absolute score offsets
    # actually, pattern should have measure offsets starting at zero, so that it can shift forward and find the ground truth offset centred aroudn the measure nubmer
    #pattern = music21.stream.Stream([score.parts[part_index].measure(n) for n in range(lower, upper + 1)])
    for elt in pattern.recurse(classFilter=('GeneralNote')):
        elt_offset_in_hierarchy = elt.getOffsetBySite(pattern.flat)
        if elt_offset_in_hierarchy < start_offset or elt_offset_in_hierarchy >= end_offset:
            pattern.remove(elt, recurse=True)
    # Make the pattern start at offset 0
    shift_amount = (-1) * pattern.flat.notes[0].getOffsetBySite(pattern.flat.notes)
    for s in pattern.recurse(streamsOnly = True):
        s.shiftElements(shift_amount, classFilterList = [music21.note.GeneralNote])

    return pattern

# TODO so you can compare occurrences with the shift ouput from algorithms
def get_offset_from_keywords(measure_data, start, voice, score):
    #TODO temp fix since sometimes there is an 'SA' voice to indicate changeafter
    if len(voice) > 1:
        voice = voice[:1]
    measure_number = int(measure_data)
    measure_loc = measure_data - measure_number # float which ranges from 0 to 1
    measure = score.parts[1].measure(measure_number) # if you don't take .parts before .measure(), the offset becomes shifted to 0. take parts[1] because in fugue #20, parts[0] is empty

    # 'start' and 'end' are quarterLength offset modifications
    start_offset = measure.offset + (measure.duration.quarterLength * measure_loc) + start
    return start_offset


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


def looper(fugues, algorithms, pattern_windows, source_windows, mismatches):
    return ((fugue, algorithm, subject, pattern_window, source_window, mismatch) for fugue in fugues for algorithm in algorithms for subject in FILTER_FOR_SUBJECT_LABELS(bach_truth['wtc-i-' + str(fugue).zfill(2)].keys()) for pattern_window in pattern_windows for source_window in source_windows for mismatch in mismatches)

def fugue_looper(fugues):
    return ((fugue, subject) for fugue in fugues for subject in FILTER_FOR_SUBJECT_LABELS(bach_truth['wtc-i-' + str(fugue).zfill(2)].keys()))

def algorithm_looper(algorithms, pattern_windows, source_windows, thresholds):
    for alg in algorithms:
        if alg.__name__ in ['P1', 'P3']:
            yield (alg, {})
        if alg.__name__ in ['S1', 'W1']:
            for source_window in source_windows:
                yield (alg, {'source_window': source_window})
        if alg.__name__ in ['P2', 'S2', 'W2']:
            for source_window in source_windows:
                for pattern_window in pattern_windows:
                    for threshold in thresholds:
                        yield (alg, {
                            'source_window' : source_window,
                            'pattern_window' : pattern_window,
                            'threshold' : threshold
                            })

def get_ground_truth_dataframe():
    gt = pd.DataFrame()

    for i in range(1,25):
        source = music21.converter.parse(BACH_FUGUE_PATH(i))
        fugue_tag = 'wtc-i-' + str(i).zfill(2)

        for subject in FILTER_FOR_SUBJECT_LABELS(bach_truth[fugue_tag].keys()):
            # GET A GROUND TRUTH DATAFRAME
            ground_truth_columns = ['fug', 'sub', 'occ', 'measure', 'start']
            ground_truth = pd.DataFrame(
                    {key : val for key, val in zip(ground_truth_columns, [i, subject, 'n/a', 'n/a', 'n/a'])},
                    range(len(bach_truth[fugue_tag][subject]['occurrences'])),
                    ground_truth_columns)

            ground_truth['occ'] = [get_offset_from_keywords(x['measure'], x['start'], x['voice'], source) for x in bach_truth[fugue_tag][subject]['occurrences']]
            ground_truth['measure'] = [x['measure'] for x in bach_truth[fugue_tag][subject]['occurrences']]
            ground_truth['start'] = [x['start'] for x in bach_truth[fugue_tag][subject]['occurrences']]
            gt = pd.concat([gt, ground_truth], ignore_index=True)

    gt.to_pickle('evaluation/ground_truth.pckl')
    return gt



PATTERN_WINDOWS = [1]
SOURCE_WINDOWS = [4,5,6,7,8]
THRESHOLDS = [x * 0.1 for x in range(6,11)] #proportional to length of pattern
def run2(fugue_indices = range(1,24), algorithms = [P1, P2, P3, S1, S2, W1, W2], settings={}, pattern_windows = PATTERN_WINDOWS, source_windows = SOURCE_WINDOWS, thresholds = THRESHOLDS):
    data_frame = pd.DataFrame()


    ### LOOP THROUGH THE SUBJECTS
    for i in fugue_indices:
        fugue_tag = 'wtc-i-' + str(i).zfill(2)

        # Get the source and the pattern here so each algy gets a fresh score to color
        source = music21.converter.parse(BACH_FUGUE_PATH(i))
        #source_notes_link, source_notes = geoAlgorithm.get_notesegments_from_score(BACH_FUGUE_PATH(i))
        for subject in FILTER_FOR_SUBJECT_LABELS(bach_truth[fugue_tag].keys()):
            print("Fetching pattern " + subject + " from fugue " + fugue_tag)
            pattern = get_pattern_from_fugue(bach_truth, fugue_tag, subject)
            if len(pattern.flat.notes) == 0:
                print("Pattern has no length.")
                logging.warning("Pattern has no length")
                continue

            ### LOOP THROUGH THE ALGORITHMS
            for algorithm, settings in algorithm_looper(algorithms, pattern_windows, source_windows, thresholds):


                ## UPDATE SETTINGS
                settings.update({
                    'parsed_input' : True,
                    'runOnInit' : False
                    })
                if settings.has_key('threshold'):
                    percent_threshold = settings['threshold']
                    settings.update({
                        'threshold' : int(len(pattern.flat.notes) * settings['threshold']) #proportional to length of pattern
                        })
                else:
                    percent_threshold = 1
                if settings.has_key('pattern_window'):
                    percent_pwindow = settings['pattern_window']
                    settings.update({
                        'pattern_window' : int(len(pattern.flat.notes) * settings['pattern_window']) #proportional to length of pattern
                        })
                else:
                    percent_pwindow = 1

                ## RUN THE ALGORITHM ##
                print("Creating algorithm object " + algorithm.__name__)
                larry = algorithm(pattern, source, settings)
                larry.settings.update({'colour' : COLOUR_SCHEMA[subject]})
                print("Running algorithm " + larry.__class__.__name__ + " on fugue " + fugue_tag + " subject " + subject + " with p_w {0}, s_w {1}, and threshold {2}".format(larry.settings['pattern_window'], larry.settings['source_window'], larry.settings['threshold']))
                try:
                    larry.run()
                except music21.stream.StreamException as e:
                    logging.error("Algorithm Failed on fugue {0}, subject {1} \n".format(fugue_tag, subject) + str(larry))
                    print(e.message)
                    continue

                ## PREPARE DATAFRAME INDICES
                df = pd.DataFrame(
                        {key : val for key, val in zip(DF_COLUMNS, [0, 'n/a', i, subject, algorithm.__name__, larry.settings['pattern_window'], percent_pwindow, larry.settings['source_window'], larry.settings['threshold'], percent_threshold, len(larry.pattern.flat.notes)])},
                        range(len(larry.occurrences)),
                        DF_COLUMNS)

                # PUT ALGORITHM RESULTS IN DATAFRAME
                df['occ'] = [x[0] for x in larry.occurrencesAsShifts]
                df['gt'] = df['occ'].isin([get_offset_from_keywords(x['measure'], x['start'], x['voice'], source) for x in bach_truth[fugue_tag][subject]['occurrences']])
                data_frame = pd.concat([data_frame, df], ignore_index=True)

            # Write one pickle per subject
            #data_frame.to_pickle('experiment/' + "_".join([str(i), subject] + '.pckl'))
        # Write one pickle per fugue
        print('Writing fugue dataframe...')
        data_frame.to_pickle('experiment2/' + str(i) + '.pckl')

        ## WRITE THE SCORE ##
        new_file_base = os.path.join(BACH_PATH, "_".join([fugue_tag, larry.__class__.__name__, "all"])) # with all subjects coloured at once

        #write_score(larry.original_source, new_file_base)

    return data_frame

def algy_table(df, alg, pw, sw, thresh):
    return df[(df['alg'] == alg) & (df['%pw'] == pw) & (df['%thresh'] == thresh) & (df['sw'] == sw)]


def precision(carl):
    if len(carl) == 0:
        return 0
    return 100*float(len(carl[carl['gt'] == True]))/float(len(carl))

def recall(carl):
    return 100*float(len(carl[carl['gt'] == True]))/float(len(gt))

def fscore(x):
    if precision(x) == 0 and recall(x) == 0:
        return 0
    return 2 * (precision(x) * recall(x)) / (precision(x) + recall(x))

pws = [x * 0.1 for x in range(1,5)]
sws = [4,5,6,7,8]
thresh = [x * 0.1 for x in range(6,11)] #proportional to length of pattern


logging.basicConfig(filename='exp.log', level=logging.DEBUG)

f = open('evaluation/fugue_truth.pckl', 'rb')
bach_truth = pickle.load(f)
f.close()

gt = pd.read_pickle('evaluation/ground_truth.pckl')

all_df = []
for f in os.walk('exps'):
    for g in f[2]:
        all_df.append(pd.read_pickle(f[0] + '/' + g))

data = pd.concat(all_df, ignore_index = True).drop_duplicates()


### TAVERN
for (dirpath, dirnames, filenames) in os.walk('tavern'):
    if os.path.basename(dirpath) == 'Krn':
        pass

# list occurrences:
#bach_truth[fugue_tag(i)][subject]['occurrences'] for subject in FILTER_FOR_SUBJECT_LABELS(bach_truth[fugue_tag(i)].keys()) for i in range(1,25)]
#df_occ_index.append(lambda x, y: x+y, larry.occurrencesAsShifts)
                #df_occ_index.append(map(lambda x: (fugue_tag, subject, x['measure']), bach_truth[fugue_tag][subject]['occurrences']))

logging.basicConfig(filename=__name__ + '.log', level=logging.INFO)
#logger
from parse_fugue_truth import parse_truth

def evaluate(algorithm):

    wtc_ground_truth = parse_truth()

