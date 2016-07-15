from collections import Counter
import os
import pandas
from vis.workflow import WorkflowManager
from vis.models.indexed_piece import IndexedPiece
from vis.analyzers.indexers import interval, dissonance, metre, noterest, ngram
from vis.analyzers.experimenters import frequency
from vis import workflow
from numpy import nan, isnan
import numpy
import six
from six.moves import range, xrange  # pylint: disable=import-error,redefined-builtin
import time
import pdb
from music21 import converter, stream, expressions, note
import array
from vis.analyzers.indexers.noterest import indexer_func as nr_ind_func
import multiprocessing as mp

# get the path to the 'vis' directory
import vis
VIS_PATH = vis.__path__[0]

pL = ['Lassus_Duets/Lassus_1_Beatus_Vir.xml',        # Lassus Duos
        'Lassus_Duets/Lassus_2_Beatus_Homo.xml',
        'Lassus_Duets/Lassus_3_Oculus.xml',
        'Lassus_Duets/Lassus_4_justus.xml',
        'Lassus_Duets/Lassus_5_Expectatio.xml',
        'Lassus_Duets/Lassus_6_Qui_Sequitur_Me.xml',
        'Lassus_Duets/Lassus_7_Justi.xml',
        'Lassus_Duets/Lassus_8_Sancti_mei.xml',
        'Lassus_Duets/Lassus_9_Qui_Vult.xml',
        'Lassus_Duets/Lassus_10_Serve_bone.xml',
        'Lassus_Duets/Lassus_11_Fulgebunt_justi.xml',
        'Lassus_Duets/Lassus_12_Sicut_Rosa.xml',

        'Morley_Duets/1 Goe yee my canzonets.xml',      # Morley Duos
        'Morley_Duets/2 When loe by break of morning.xml',
        'Morley_Duets/3 Sweet nymph.xml',
        'Morley_Duets/5 I goe before my darling.xml',
        'Morley_Duets/6 La Girandola.xml',
        'Morley_Duets/7 Miraculous loves wounding.xml',
        'Morley_Duets/8 Lo heere another love.xml',
        'Morley_Duets/11 Fyre and Lightning.xml',
        'Morley_Duets/13 Flora wilt thou torment mee.xml',
        'Morley_Duets/15 In nets of golden wyers.xml',
        'Morley_Duets/17 O thou that art so cruell.xml',
        'Morley_Duets/19 I should for griefe and anguish.xml',

        'Josquin_Duets/Agnus Dei.xml',                  # Josquin Duos
        'Josquin_Duets/Crucifixus.xml',
        'Josquin_Duets/Et incarnatus est.xml',
        'Josquin_Duets/Missa_Ad_Fugam_Sanctus_version_2_Benedictus.xml',
        'Josquin_Duets/Missa_Ad_fugam_Sanctus_version_2_Pleni.xml',
        'Josquin_Duets/Missa_Ad_fugam_Sanctus_version_2_Qui_venit.xml',
        'Josquin_Duets/Missa_Allez_regretz_I_Sanctus_Pleni.xml',
        'Josquin_Duets/Missa_Ave_maris_stella_Sanctus_Benedictus.xml',
        'Josquin_Duets/Missa_Ave_maris_stella_Sanctus_Qui_venit.xml',
        'Josquin_Duets/Missa_Pange_lingua_Sanctus_Benedictus.xml',
        'Josquin_Duets/Missa_Pange_lingua_Sanctus_Pleni_sunt_celi.xml',
        'Josquin_Duets/Qui edunt me.xml'
        ]

opera = float(len(pL))
setts = {'quality': True, 'simple or compound': 'simple'}
horiz_setts = {'quality': False, 'simple or compound': 'compound'}
n_setts = {'n': 3, 'horizontal': [('horiz', '1')], 'vertical': [('vert', '0,1')],
                 'mark_singles': False}
dicts = []
all_ngrams = []
layer = []
res = []

#def get_ngrams(path):
for i, path in enumerate(pL):
    ind_piece = IndexedPiece(path)
    parts_nr = []
    test_piece = converter.parse(path)
    part_numbers = range(len(test_piece.parts))

    for x in part_numbers:
        temp_part = test_piece.parts[x]
        nr = []
        part_index = []
        for event in temp_part.recurse():
            if 'Note' in event.classes or 'Rest' in event.classes:
                if hasattr(event, 'tie') and event.tie is not None and event.tie.type in ('stop', 'continue'):
                    # dur[-1] += event.quarterLength
                    continue
                nr.append(nr_ind_func((event,)))
                for y in event.contextSites():
                    if y[0] is temp_part:
                        part_index.append(y[1])

        parts_nr.append(pandas.Series(nr, index=part_index))

    basic_nr = pandas.concat([s for s in parts_nr], axis=1)

    part_strings = []
    for num in part_numbers:
        part_strings.append(unicode(num))

    iterables = [['basic.NoteRestIndexer'], part_strings]
    basic_nr_multi_index = pandas.MultiIndex.from_product(iterables, names = ['Indexer', 'Parts'])
    basic_nr.columns = basic_nr_multi_index

    horiz = interval.HorizontalIntervalIndexer(basic_nr, horiz_setts).run()
    vert_ints = interval.IntervalIndexer(basic_nr, setts).run()


    test_wm = WorkflowManager([path])
    test_wm.load('pieces')
    test_wm.settings(0, 'voice combinations', 'all pairs')
    test_wm.settings(0, 'n', 2)
    test_wm.settings(0, 'continuer', '_')
    n_grams = test_wm.run('interval n-grams')
    #all_ngrams.append(n_grams)
    ser = n_grams.iloc[:, 0]
    dikt = Counter(ser.to_dict())
    dicts.append(dikt)
    print 'N-gram analysis %d percent complete' % ((i+1)/opera*100) #Change %d to %f for float values
    #in_val = pandas.concat((horiz, vert_ints), axis=1)
    #n_grams = ngram.NGramIndexer(in_val, n_setts).run()

numPieces = len(dicts)
comparisons = numPieces*(numPieces-1)/2.0
count = 0
new_clusters = []
for j, pieceA in enumerate(dicts):
    for k, pieceB in enumerate(dicts[j+1:]):
        cluster = pieceA + pieceB
        a_total = sum(pieceA.values())
        b_total = sum(pieceB.values())
        c_total = float(sum(cluster.values()))
        percA = a_total/c_total # out of 1, not out of 100
        percB = b_total/c_total
        similarity = 0.0
        count += 1
        for n in cluster.iterkeys(): # Each n is the name of an n-grams
            a_ideal = cluster[n] * percA
            b_ideal = cluster[n] * percB
            a_acc = 1 - abs(pieceA[n] - a_ideal)/cluster[n]
            b_acc = 1 - abs(pieceB[n] - b_ideal)/cluster[n]
            n_perc = cluster[n]/c_total
            similarity += a_acc * b_acc * n_perc * 100
        res.append((round(similarity, 2), j+1, j+k+2))
        #layer.append((similarity, j+1, j+k+2))
        #new_clusters.append(cluster)



    print '%d percent done with n-gram profile comparisons' % (count/comparisons*100)
#indx = layer.index(max(layer))
#dicts.remove(max(layer[indx][1], layer[indx][2]))
#dicts.remove(min(layer[indx][1], layer[indx][2]))
#dicts.append(new_clusters[indx])

print res
pdb.set_trace()
