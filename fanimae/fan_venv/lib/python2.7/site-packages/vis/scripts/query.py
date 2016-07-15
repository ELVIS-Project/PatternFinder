import os
import pandas as pd
from vis.workflow import WorkflowManager
from vis.models.indexed_piece import IndexedPiece
from vis.analyzers.indexers import interval, dissonance, metre, noterest, ngram, offset
from vis.analyzers.experimenters import frequency, dendrogram
from numpy import nan, isnan, array
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

Josquin = [
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
Lassus = [
        'Lassus_Duets/Lassus_1_Beatus_Vir.xml',        # Lassus Duos
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
        'Lassus_Duets/Lassus_12_Sicut_Rosa.xml'
        ]
Morley = [
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
        'Morley_Duets/19 I should for griefe and anguish.xml'
        ]

piece_path = '/home/amor/Code/vis-framework/vis/scripts/Agnus-dei_Ockeghem,-Jean-de_file1.mus'

duo_sets = (Josquin, Lassus, Morley)
composers = ('Josquin', 'Lassus', 'Morley')
composer_results = []
indx = ('M6 P1 P5', 'm6 P1 P5', 'M6 M2 P5', 'm6 m2 P5', 'P5 P1 M6', 'P5 P1 m6', 'P5 -M2 M6', 'P5 -m2 m6', 'Total 2-grams')

v_setts = {'quality': True, 'simple or compound': 'simple', 'direction': False}
h_setts = {'quality': True, 'horiz_attach_later': True, 'continuer': 'P1', 'simple or compound': 'compound'}
n_setts = {'n': 2, 'horizontal': [('interval.HorizontalIntervalIndexer', '1')],
            'vertical': [('interval.IntervalIndexer', '0,1')], 'mark_singles': False}

pdb.set_trace()

for i, pL in enumerate(duo_sets):
    if i == 2:
        f_setts = {'quarterLength': 1.0, 'method':'ffill'}
    else:
        f_setts = {'quarterLength': 2.0, 'method':'ffill'}
    nr_dfs = []
    horiz = []
    vert = []
    total = []
    for path in pL:
        parts_nr = []
        test_piece = converter.parse(path)
        part_numbers = range(len(test_piece.parts))
        from vis.analyzers.indexers.noterest import indexer_func as nr_ind_func
        for x in part_numbers:
            temp_part = test_piece.parts[x]
            nr = []
            part_index = []
            for event in temp_part.recurse():
                if 'Note' in event.classes or 'Rest' in event.classes:
                    if hasattr(event, 'tie') and event.tie is not None and event.tie.type in ('stop', 'continue'):
                        continue
                    nr.append(nr_ind_func((event,)))
                    for y in event.contextSites():
                        if y[0] is temp_part:
                            part_index.append(y[1])

            parts_nr.append(pd.Series(nr, index=part_index))

        basic_nr = pd.concat([s for s in parts_nr], axis=1)
        
        part_strings = []
        for num in part_numbers:
            part_strings.append(unicode(num))
        
        iterables = [['basic.NoteRestIndexer'], part_strings]
        basic_nr_multi_index = pd.MultiIndex.from_product(iterables, names = ['Indexer', 'Parts'])
        basic_nr.columns = basic_nr_multi_index

        filtered_notes = offset.FilterByOffsetIndexer(basic_nr, f_setts).run()
        nr_dfs.append(filtered_notes)
        horiz.append(interval.HorizontalIntervalIndexer(nr_dfs[-1], h_setts).run())
        vert.append(interval.IntervalIndexer(nr_dfs[-1], v_setts).run())

        comb_df = pd.concat([horiz[-1], vert[-1]], axis=1)
        ngrams = ngram.NGramIndexer(comb_df, n_setts).run()
        ngram_freqs = frequency.FrequencyExperimenter(ngrams).run()
        total.append(ngram_freqs[0])

    all_duos = pd.concat(total, axis=1)
    agg = all_duos.sum(axis=1).to_frame()
    vals = []
    for x in indx[:-1]:
        vals.append((str(round(agg.at[x, 0] * 100/sum(agg.values)[0], 2)) + '%'))
    # vals = [(str(agg.at[x, 0]/round(sum(agg.values)[0]*100, 2)) + '%'), for x in indx[:-1]]
    vals.append(sum(agg.values)[0])
    ser = pd.Series(vals, index=indx)
    composer_results.append(ser)
    print '*****' + composers[i] + '*****'
    print 'M6 P1 P5:   ' + str(agg.at['M6 P1 P5', 0] * 100/sum(agg.values)[0]) + '%'
    print 'm6 P1 P5:   ' + str(agg.at['m6 P1 P5', 0] * 100/sum(agg.values)[0]) + '%'
    print 'M6 M2 P5:   ' + str(agg.at['M6 M2 P5', 0] * 100/sum(agg.values)[0]) + '%'
    print 'm6 m2 P5:   ' + str(agg.at['m6 m2 P5', 0] * 100/sum(agg.values)[0]) + '%'
    print 'P5 P1 M6:   ' + str(agg.at['P5 P1 M6', 0] * 100/sum(agg.values)[0]) + '%'
    print 'P5 P1 m6:   ' + str(agg.at['P5 P1 m6', 0] * 100/sum(agg.values)[0]) + '%'
    print 'P5 -M2 M6:  ' + str(agg.at['P5 -M2 M6', 0] * 100/sum(agg.values)[0]) + '%'
    print 'P5 -m2 m6:  ' + str(agg.at['P5 -m2 m6', 0] * 100/sum(agg.values)[0]) + '%'

    print 'Total 2-grams: ' + str(sum(agg.values)[0])


    # print '*****' + composers[i] + '*****'
    # print '6 _ 5:   ' + str(agg.at['6 _ 5', 0])
    # print '6 2 5:   ' + str(agg.at['6 2 5', 0])
    # print '5 _ 6:   ' + str(agg.at['5 _ 6', 0])
    # print '5 -2 6:  ' + str(agg.at['5 -2 6', 0])

df = pd.concat(composer_results, axis=1)
df.columns = composers
print df
pdb.set_trace()