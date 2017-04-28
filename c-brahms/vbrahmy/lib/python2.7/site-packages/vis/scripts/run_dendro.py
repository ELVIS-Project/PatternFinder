import os
import pandas as pd
from vis.workflow import WorkflowManager
from vis.models.indexed_piece import IndexedPiece
from vis.analyzers.indexers import interval, dissonance, metre, noterest, ngram, offset
from vis.analyzers.experimenters import frequency, dendrogram
from numpy import nan, isnan, array
import numpy as np
import six
import time
import pdb
from music21 import converter
from music21 import interval as m21interval
import array
from vis.analyzers.indexers.noterest import indexer_func as nr_ind_func
import multiprocessing as mp
import matplotlib.pyplot as plt

# get the path to the 'vis' directory
import vis
VIS_PATH = vis.__path__[0]


pL = [
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
        'Josquin_Duets/Qui edunt me.xml',

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
        'Morley_Duets/19 I should for griefe and anguish.xml'
        ]

opera = float(len(pL))
f_setts = {'quarterLength': 2.0, 'method':'ffill'}
v_setts = {'quality': True, 'simple or compound': 'simple', 'direction': False}
h_setts = {'quality': False, 'horiz_attach_later': True, 'simple or compound': 'compound'}
n_setts = {'n': 2, 'horizontal': [('interval.HorizontalIntervalIndexer', '1')],
            'vertical': [('interval.IntervalIndexer', '0,1')], 'mark_singles': False}
piece_lengths = []


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
        df.index = [x if x in ('P5', 'P4', 'd5', 'A4', 'Rest') else str(m21interval.Interval(x).intervalClass) for x in df.index]
    else:
        df.index = [x if x in ('Rest') else str(m21interval.Interval(x).intervalClass) for x in df.index]

    return df.reset_index().groupby('index').sum()


def run_vis(pathnames, opera, f_setts, h_setts, v_setts, n_setts):
    t1 = time.time()
    sers = []

    for i, path in enumerate(pathnames):
        ind_piece = IndexedPiece(path)
        parts_nr = []
        test_piece = converter.parse(path)
        part_numbers = range(len(test_piece.parts))
        if i == 24:
            f_setts = {'quarterLength': 1.0, 'method':'ffill'}

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

        piece_lengths.append(basic_nr.index[-1])
        if i > 23:
            piece_lengths[-1] *= 2

        filtered_notes = offset.FilterByOffsetIndexer(basic_nr, f_setts).run()

        # horiz = interval.HorizontalIntervalIndexer(filtered_notes, h_setts).run()
        vert = interval.IntervalIndexer(filtered_notes, v_setts).run()
        vert_freqs = frequency.FrequencyExperimenter(vert).run()[0]
        # vert_freqs.columns = range(len(vert_freqs.columns))

        # pseudo_ic = i_class(vert_freqs, rests=True, modRen=True)
        sers.append(vert_freqs.iloc[:, 0])

        # comb_df = pd.concat([horiz, vert], axis=1)
        # n_grams = ngram.NGramIndexer(comb_df, n_setts).run()
        # ngram_freqs = frequency.FrequencyExperimenter(n_grams).run()[0]

        # sers.append(ngram_freqs.iloc[:, 0])
        print 'Analysis %d percent complete' % ((i+1)/opera*100) #Change %d to %f for float values

    t2 = time.time()
    print 'VIS Analysis took %f seconds.' % round((t2-t1), 2)
    return sers




graph_settings = {
                  'label_connections': False,
                  'connection_string': 'r.',
                  'linkage_type': 'average',
                  'xlabel': 'Interval Analyses: Josquin = 1-12; Lassus = 13-24; Morley = 25-36',
                  'ylabel': 'Percent Dissimilarity',
                  'title': 'Josquin Lassus and Morley Duet Intervallic Dissimilarity',
                  'interactive_dendrogram': False,
                  'filename_and_type': VIS_PATH[:-3] + '36_JLM_Duets_Interval_Dendrogram.pdf', # .pdf and .png (default) are the only possible formats
                  'return_data': False
                  }
dendrogram_settings = {
                           'p': 40,
                           'truncate_mode': None,
                           'color_threshold': 21.5,
                           'get_leaves': True,
                           'orientation': 'top',
                           'labels': None,
                           'count_sort': False,
                           'distance_sort': False,
                           'show_leaf_counts': True,
                           'no_plot': False,
                           'no_labels': False,
                           'color_list': None,
                           'leaf_font_size': 10,
                           'leaf_rotation': -90,
                           'leaf_label_func': None,
                           'no_leaves': False,
                           'show_contracted': False,
                           'link_color_func': None,
                           'ax': None,
                           'above_threshold_color': 'b'
                           }

sers = [run_vis(pL, opera, f_setts, h_setts, v_setts, n_setts)]
t2 = time.time()
interval_results = pd.concat(sers[0], axis=1, ignore_index=True)
interval_results = interval_results[interval_results.index != 'Rest']
interval_results = interval_results.replace(to_replace='NaN', value=0)
interval_results = interval_results.div(list(interval_results.sum()))
interval_results = interval_results*100
interval_results.columns = range(1, 1 + len(pL))
# interval_results.to_csv(VIS_PATH+'_36_interval_qual_no_rests_dfs.csv', index_label='Intervals')
corrs = interval_results.corr()
corrs.to_csv(VIS_PATH+'_36_interval_qual_no_rests_correlations.csv')
# plt.pcolor(corrs)
# plt.yticks(np.arange(0.5, len(corrs.index), 1), corrs.index)
# plt.xticks(np.arange(0.5, len(corrs.columns), 1), corrs.columns)
# plt.show()

# query = dendrogram.HierarchicalClusterer(sers, graph_settings=graph_settings, dendrogram_settings=dendrogram_settings).run()
t3 = time.time()
print 'Clustering took %f seconds.' % round((t3-t2), 2)
pdb.set_trace()

# pd.Series(piece_lengths, index=range(1, 37))
