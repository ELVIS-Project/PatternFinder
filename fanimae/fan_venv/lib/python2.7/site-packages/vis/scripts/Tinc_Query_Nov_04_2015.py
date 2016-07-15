
import os
import pandas as pd
from vis.workflow import WorkflowManager
from vis.models.indexed_piece import IndexedPiece
from vis.analyzers.indexers import dissonance, metre, noterest, offset, ngram, interval
from vis.analyzers.indexers import qualityControl as qc
from vis.analyzers.experimenters import frequency
from vis import workflow
from numpy import nan, isnan
import numpy
import six
import time
import pdb
import array

# get the path to the 'vis' directory
import vis
VIS_PATH = vis.__path__[0]


# piece_path = "/home/amor/Code/vis-framework/vis/tests/corpus/Kyrie.krn"
# piece_path = '/home/amor/Code/vis-framework/vis/tests/corpus/Jos2308.mei'
# piece_path = '/home/amor/Code/vis-framework/vis/scripts/Morley_Duets/6 La Girandola.xml'
folder_path = '/home/amor/Code/vis-framework/vis/scripts/Tinc_favs_Nov_17_2015'
# ind_piece = IndexedPiece(piece_path)
pickle_path = '/home/amor/Code/vis-framework/vis/scripts/TincQPickles/'
csv_path = '/home/amor/Code/vis-framework/vis/scripts/TincQCSVs/'

eighth = []
quarter = []
half = []
whole = []

piece_paths = []
for root, dirs, files in os.walk(folder_path):
    for folder in dirs:
        folder_r_path = folder_path + '/' + folder
        for root_r, dirs_r, files_r in os.walk(folder_r_path):
            for name in files_r:
                if folder == 'Eighth':
                    eighth.append(folder_r_path + '/' + name)
                if folder == 'Quarter':
                    quarter.append(folder_r_path + '/' + name)
                if folder == 'Half':
                    half.append(folder_r_path + '/' + name)
                if folder == 'Whole':
                    whole.append(folder_r_path + '/' + name)

# measures = metre.MeasureIndexer(test_piece.parts).run()
# filter_setts = {'quarterLength': 2.0, 'method':'ffill'}
# filtered_notes = offset.FilterByOffsetIndexer(actual, filter_setts).run()

v_setts = {'quality': True, 'simple or compound': 'compound', 'direction': False}
v_nq_setts = {'quality': False, 'simple or compound': 'compound', 'direction': False}
h_setts = {'quality': False, 'horiz_attach_later': False, 'simple or compound': 'compound', 'direction': True}
h_later_setts = {'quality': False, 'horiz_attach_later': True, 'simple or compound': 'compound', 'direction': True}
n_setts_list = [{'n': 2, 'horizontal': [('interval.HorizontalIntervalIndexer', '1')], 'vertical': [('interval.IntervalIndexer', '0,1')], 'mark_singles': False, 'continuer': '1', 'terminator': ['Rest']},
                {'n': 2, 'horizontal': [('interval.HorizontalIntervalIndexer', '2')], 'vertical': [('interval.IntervalIndexer', '0,2')], 'mark_singles': False, 'continuer': '1', 'terminator': ['Rest']},
                {'n': 2, 'horizontal': [('interval.HorizontalIntervalIndexer', '2')], 'vertical': [('interval.IntervalIndexer', '1,2')], 'mark_singles': False, 'continuer': '1', 'terminator': ['Rest']},
                {'n': 2, 'horizontal': [('interval.HorizontalIntervalIndexer', '3')], 'vertical': [('interval.IntervalIndexer', '0,3')], 'mark_singles': False, 'continuer': '1', 'terminator': ['Rest']},
                {'n': 2, 'horizontal': [('interval.HorizontalIntervalIndexer', '3')], 'vertical': [('interval.IntervalIndexer', '1,3')], 'mark_singles': False, 'continuer': '1', 'terminator': ['Rest']},
                {'n': 2, 'horizontal': [('interval.HorizontalIntervalIndexer', '3')], 'vertical': [('interval.IntervalIndexer', '2,3')], 'mark_singles': False, 'continuer': '1', 'terminator': ['Rest']},
                ]

other_voices = []
nr_list = []
dur_list = []
h_list = []
f_list = []
h_later_list = []
h_l_f_list = []
v_list = []
v_nq_list = []
v_f_list = []
v_f_nq_list = []
two_gram_list = []
two_gram_nq_list = []
two_gram_list_f = []
two_gram_nq_list_f = []
offsets = (.5, 1, 2, 4)
file_sets = (eighth, quarter, half, whole)

for h, off in enumerate(offsets):
    f_setts = {'quarterLength': off, 'method':'ffill'}
    group = file_sets[h]
    for i, piece in enumerate(group):
        print str(h+1) + '.' + str(i) + ': ' + piece
        ind_piece = IndexedPiece(piece)
        test_piece = ind_piece._import_score()
        test_parts = test_piece.parts
        actual = ind_piece.get_data([noterest.NoteRestIndexer])
        nr_list.append(actual)
        dur = metre.DurationIndexer(test_parts).run()
        dur_list.append(dur)
        horiz = interval.HorizontalIntervalIndexer(actual, h_setts).run()
        filtered = offset.FilterByOffsetIndexer(actual, f_setts).run()
        f_list.append(filtered)
        h_list.append(horiz)
        horiz_later = interval.HorizontalIntervalIndexer(actual, h_later_setts).run()
        h_later_list.append(horiz_later)
        horiz_later_f = interval.HorizontalIntervalIndexer(filtered, h_later_setts).run()
        h_l_f_list.append(horiz_later_f)
        vert = interval.IntervalIndexer(actual, v_setts).run()
        v_list.append(vert)
        vert_nq = interval.IntervalIndexer(actual, v_nq_setts).run()
        v_nq_list.append(vert_nq)
        vert_f = interval.IntervalIndexer(filtered, v_setts).run()
        v_f_list.append(vert_f)
        vert_f_nq = interval.IntervalIndexer(filtered, v_nq_setts).run()
        v_f_nq_list.append(vert_f_nq)
        comb_df = pd.concat([horiz_later, vert], axis=1)
        comb_df_nq = pd.concat([horiz_later, vert_nq], axis=1)
        comb_df_f = pd.concat([horiz_later_f, vert_f], axis=1)
        comb_df_f_nq = pd.concat([horiz_later_f, vert_f_nq], axis=1)

        if len(dur.columns) == 2:
            n_setts = n_setts_list[:1]
        elif len(dur.columns) == 3:
            n_setts = n_setts_list[:3]
        elif len(dur.columns) == 4:
            n_setts = n_setts_list[:]
        else:
            other_voices.append(len(dur.columns))
        for pair in n_setts:
            these_n_setts = pair
            ngrams = ngram.NGramIndexer(comb_df, these_n_setts).run()
            ngrams_nq = ngram.NGramIndexer(comb_df_nq, these_n_setts).run()
            ngrams_f = ngram.NGramIndexer(comb_df_f, these_n_setts).run()
            ngrams_f_nq = ngram.NGramIndexer(comb_df_f_nq, these_n_setts).run()
            two_gram_list.append(ngrams)
            two_gram_nq_list.append(ngrams_nq)
            two_gram_list_f.append(ngrams_f)
            two_gram_nq_list_f.append(ngrams_f_nq)

temp = pd.concat(h_list)
temp.to_pickle(pickle_path + 'h_list')
all_h = temp.stack().stack().value_counts()
all_h.to_csv(csv_path + 'all_h.csv')

temp = pd.concat(h_l_f_list)
temp.to_pickle(pickle_path + 'h_l_f_list')
all_h_l_f = temp.stack().stack().value_counts()
all_h_l_f.to_csv(csv_path + 'all_h_l_f.csv')

temp = pd.concat(nr_list)
temp.to_pickle(pickle_path + 'nr_list')
all_nr = temp.stack().stack().value_counts()
all_nr.to_csv(csv_path + 'all_nr.csv')

temp = pd.concat(dur_list)
temp.to_pickle(pickle_path + 'dur_list')
all_dur = temp.stack().stack().value_counts()
all_dur.to_csv(csv_path + 'all_dur.csv')

temp = pd.concat(f_list)
temp.to_pickle(pickle_path + 'f_list')
all_f = temp.stack().stack().value_counts()
all_f.to_csv(csv_path + 'all_f.csv')

temp = pd.concat(v_list)
temp.to_pickle(pickle_path + 'v_list')
all_v = temp.stack().stack().value_counts()
all_v.to_csv(csv_path + 'all_v.csv')

temp = pd.concat(v_f_list)
temp.to_pickle(pickle_path + 'v_f_list')
all_v_f = temp.stack().stack().value_counts()
all_v_f.to_csv(csv_path + 'all_v_f.csv')

temp = pd.concat(two_gram_list)
temp.to_pickle(pickle_path + 'two_gram_list')
all_two_gram = temp.stack().stack().value_counts()
all_two_gram.to_csv(csv_path + 'all_two_gram.csv')

temp = pd.concat(two_gram_nq_list)
temp.to_pickle(pickle_path + 'two_gram_nq_list')
all_two_gram_nq = temp.stack().stack().value_counts()
all_two_gram_nq.to_csv(csv_path + 'all_two_gram_nq.csv')

temp = pd.concat(two_gram_list_f)
temp.to_pickle(pickle_path + 'two_gram_list_f')
all_two_gram_f = temp.stack().stack().value_counts()
all_two_gram_f.to_csv(csv_path + 'all_two_gram_f.csv')

temp = pd.concat(two_gram_nq_list_f)
temp.to_pickle(pickle_path + 'two_gram_nq_list_f')
all_two_gram_nq_f = temp.stack().stack().value_counts()
all_two_gram_nq_f.to_csv(csv_path + 'all_two_gram_nq_f.csv')




pdb.set_trace()

# horiz = interval.HorizontalIntervalIndexer(actual, h_setts).run()


# vert = interval.IntervalIndexer(actual, v_setts).run()
# comb_df = pd.concat([horiz, vert], axis=1)
# ngrams = ngram.NGramIndexer(comb_df, n_setts).run()


# pdb.set_trace()




# passes = []
# fails = []
# qc_results = []
# tally = 0

# for j, peace in enumerate(piece_paths):
#     print str(j)
#     print peace
#     test = qc.QualityControl()
#     result = test.measure_checker(peace)
#     print result[0]
#     print result[1]
#     print '**********'
#     if result[0]:
#         tally += 1
#         passes.append((j, peace, result))
#     else:
#         fails.append((j, peace, result))
#         ind_piece = IndexedPiece(peace)
#         test = ind_piece._import_score()
#         test = test.parts
#         ms = metre.MeasureIndexer(test).run()
#         nr = noterest.NoteRestIndexer(test).run()
#         pdb.set_trace()
#     qc_results.append((j, peace, result))

# pdb.set_trace()