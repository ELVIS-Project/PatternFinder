
import os
import pandas as pd
from vis.workflow import WorkflowManager
from vis.models.indexed_piece import IndexedPiece
from vis.analyzers.indexers import dissonance, metre, noterest, offset, ngram
from vis.analyzers.indexers import interval as ntrvl
from vis.analyzers.experimenters import frequency
from vis import workflow
from numpy import nan, isnan
import numpy
import six
from six.moves import range, xrange  # pylint: disable=import-error,redefined-builtin
import time
import pdb
from music21 import interval
import array

# get the path to the 'vis' directory
import vis
VIS_PATH = vis.__path__[0]


# piece_path = "/home/amor/Code/vis-framework/vis/tests/corpus/Kyrie.krn"
# piece_path = "/home/amor/Code/vis-framework/vis/tests/corpus/bwv603.xml"
# piece_path = "/home/amor/Code/vis-framework/vis/tests/corpus/madrigal51.mxl"
# piece_path = '/home/amor/Code/vis-framework/vis/scripts/Karens_Pieces/qui_secuntur.mei'
# piece_path = '/home/amor/Code/vis-framework/vis/tests/corpus/Reimenschnieder/1-026900B_.xml'
# piece_path = '/home/amor/Code/vis-framework/vis/tests/corpus/Jos2308.mei'
# piece_path = '/home/amor/Code/vis-framework/vis/tests/corpus/Sanctus.krn'
# piece_path = '/home/amor/Code/vis-framework/vis/tests/corpus/Kyrie_short.krn'
piece_path = '/home/amor/Code/vis-framework/vis/scripts/Morley_Duets/6 La Girandola.xml'
folder_path = '/home/amor/Code/vis-framework/vis/scripts/Lassus_Duets/'
# ind_piece = IndexedPiece(piece_path)


# bwv603 = converter.parse(os.path.join(VIS_PATH, 'tests', 'corpus/bwv603.xml'))
# test_part = [bwv603.parts[0], bwv603.parts[1], bwv603.parts[2], bwv603.parts[3]]



# test_piece = ind_piece._import_score()
# test_parts = test_piece.parts
# actual = ind_piece.get_data([noterest.NoteRestIndexer]) 
piece_paths = []
for root, dirs, files in os.walk(folder_path):
    for name in files:
        piece_paths.append(folder_path + name)

wm = WorkflowManager(piece_paths)

# measures = metre.MeasureIndexer(test_piece.parts).run()

pdb.set_trace()

# filter_setts = {'quarterLength': 2.0, 'method':'ffill'}
# filtered_notes = offset.FilterByOffsetIndexer(actual, filter_setts).run()

v_setts = {'quality': True, 'simple or compound': 'simple', 'direction': False}
h_setts = {'quality': False, 'horiz_attach_later': True, 'simple or compound': 'simple', 'direction': False}
n_setts = {'n': 2, 'horizontal': [('interval.HorizontalIntervalIndexer', '1')], 'vertical': [('interval.IntervalIndexer', '0,1')],
                 'mark_singles': False}

def i_class(df, rests=True, modRen=False):
    """
    Takes the results of the IntervalIndexer and compresses most intervals to their 
    interval-class equivalents (an integer between zero and 6 inclusive, represented as 
    strings), so for example major sixths get combined with minor thirds in the category '3'. 
    Note that the intervals can be calculated as either simple or compound, however they must 
    be calculated with qualtiy. There are two exceptions....
    """
    if not rests:
        df = df[df.index != 'Rest']
    if modRen:
        df.index = [x if x in ('P5', 'P4', 'd5', 'A4', 'Rest') else str(interval.Interval(x).intervalClass) for x in df.index]
    else:
        df.index = [x if x in ('Rest') else str(interval.Interval(x).intervalClass) for x in df.index]

    return df.reset_index().groupby('index').sum()


verts = ntrvl.IntervalIndexer(actual, v_setts).run()
verts = frequency.FrequencyExperimenter(verts).run()[0]
# verts = verts[verts.index != 'Rest']
verts.columns = range(len(verts.columns))
iced = i_class(verts)
pdb.set_trace()
# verts = verts.stack().stack().value_counts()
df = i_class(verts)

# v_int_freqs = frequency.FrequencyExperimenter(verts).run()[0]
# results = i_class(v_int_freqs)


pdb.set_trace()

horiz = interval.HorizontalIntervalIndexer(actual, h_setts).run()


vert = interval.IntervalIndexer(actual, v_setts).run()
comb_df = pd.concat([horiz, vert], axis=1)
ngrams = ngram.NGramIndexer(comb_df, n_setts).run()


pdb.set_trace()
# comb_df = pd.concat([horiz, vert], axis=1)
# n_setts = {'n': 2, 'horizontal': [('interval.HorizontalIntervalIndexer', '1')], 'vertical': [('interval.IntervalIndexer', '0,1')],
#                  'mark_singles': False}
# ngrams = ngram.NGramIndexer(comb_df, n_setts).run()
# ngram_freqs = frequency.FrequencyExperimenter(ngrams).run()

# pdb.set_trace()


# n1 = note.Note('g5')
# n2 = note.Note('e4')
# verts = []
# horis = []

# for x in range(10):
#     t0 = time.time()
#     y = interv.IntervalIndexer(actual, v_setts).run()
#     t1 = time.time()
#     verts.append(t1-t0)

# for x in range(10):
#     t0 = time.time()
#     z = interv.HorizontalIntervalIndexer(actual, h_setts).run()
#     t1 = time.time()
#     horis.append(t1-t0)

# print 'Vertical Indexer Runtime:   ' + str(min(verts))
# print 'Horizontal Indexer Runtime: ' + str(min(horis))