
import os
import pandas as pd
from vis.workflow import WorkflowManager
from vis.models.indexed_piece import IndexedPiece
from vis.analyzers.indexers import dissonance, metre, noterest, offset, ngram, interval
from vis.analyzers.experimenters import frequency
from vis import workflow
from numpy import nan, isnan
import numpy
import six
from six.moves import range, xrange  # pylint: disable=import-error,redefined-builtin
import time
import pdb
import array

# get the path to the 'vis' directory
import vis
VIS_PATH = vis.__path__[0]


piece_path = "/home/amor/Code/vis-framework/vis/tests/corpus/Kyrie.krn"
# piece_path = "/home/amor/Code/vis-framework/vis/tests/corpus/bwv603.xml"
# piece_path = "/home/amor/Code/vis-framework/vis/tests/corpus/madrigal51.mxl"
# piece_path = '/home/amor/Code/vis-framework/vis/scripts/Karens_Pieces/qui_secuntur.mei'
# piece_path = '/home/amor/Code/vis-framework/vis/tests/corpus/Reimenschnieder/1-026900B_.xml'
# piece_path = '/home/amor/Code/vis-framework/vis/tests/corpus/Jos2308.mei'
# piece_path = '/home/amor/Code/vis-framework/vis/tests/corpus/Sanctus.krn'
# piece_path = '/home/amor/Code/vis-framework/vis/tests/corpus/Kyrie_short.krn'
# piece_path = '/home/amor/Code/vis-framework/vis/scripts/Morley_Duets/6 La Girandola.xml'
ind_piece = IndexedPiece(piece_path)


# bwv603 = converter.parse(os.path.join(VIS_PATH, 'tests', 'corpus/bwv603.xml'))
# test_part = [bwv603.parts[0], bwv603.parts[1], bwv603.parts[2], bwv603.parts[3]]


test_piece = ind_piece._import_score()
test_parts = test_piece.parts
actual = ind_piece.get_data([noterest.NoteRestIndexer]) 


measures = metre.MeasureIndexer(test_piece.parts).run()

# pdb.set_trace()

# filter_setts = {'quarterLength': 2.0, 'method':'ffill'}
# filtered_notes = offset.FilterByOffsetIndexer(actual, filter_setts).run()
v_setts = {'quality': 'interval class', 'simple or compound': 'simple', 'directed': False}
h_setts = {'quality': False, 'horiz_attach_later': True, 'simple or compound': 'simple', 'directed': False}
n_setts = {'n': 2, 'horizontal': [('interval.HorizontalIntervalIndexer', '1')], 'vertical': [('interval.IntervalIndexer', '0,1')],
                 'mark_singles': False}


for x in range(1):
    t0 = time.time()
    vert = interval.IntervalIndexer(actual, v_setts).run()
    t1 = time.time()
    print str(t1-t0)
    # runtimes.append(t1-t0)

# print 'Best runtime with ' + analysis_strings[w] + ' : ' + str(min(runtimes))
# print 'Avg. runtime with ' + analysis_strings[w] + ' : ' + str(sum(runtimes)/len(runtimes))
# print '*****************'



pdb.set_trace()
