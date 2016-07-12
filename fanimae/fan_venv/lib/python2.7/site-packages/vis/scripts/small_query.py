import os
import pandas
from vis.workflow import WorkflowManager
from vis.models.indexed_piece import IndexedPiece
from vis.analyzers.indexers import interval, dissonance, metre, noterest, offset, ngram
from vis.analyzers.experimenters import frequency, aggregator
from vis import workflow
from numpy import nan, isnan
import numpy
import six
from six.moves import range, xrange  # pylint: disable=import-error,redefined-builtin
import time
import pdb
from music21 import converter, stream, expressions, note
import array

# get the path to the 'vis' directory
import vis
VIS_PATH = vis.__path__[0]
piece_path = "/home/amor/Code/vis-framework/vis/tests/corpus/Kyrie.krn"

ind_piece = IndexedPiece(piece_path)
test_piece = ind_piece._import_score()
parts = test_piece.parts

nr = noterest.NoteRestIndexer(parts).run()
dr = metre.DurationIndexer(parts).run()
ms = metre.MeasureIndexer(parts).run()
vt = interval.IntervalIndexer(nr).run()
# n_setts = {'n': 3, 'vertical': [('metre.DurationIndexer', '0')], 'mark_singles': True}
# upper_ng = ngram.NGramIndexer(dr, n_setts).run()
# n_setts = {'n': 3, 'vertical': [('metre.DurationIndexer', '1')], 'mark_singles': True}
# lower_ng = ngram.NGramIndexer(dr, n_setts).run()
# upper_counts = frequency.FrequencyExperimenter(upper_ng).run()[0]
# lower_counts = frequency.FrequencyExperimenter(lower_ng).run()[0]

pdb.set_trace()

# 'horizontal': [('interval.HorizontalIntervalIndexer', '1')], 
