import os
import pandas as pd
from vis.workflow import WorkflowManager
from vis.models.indexed_piece import IndexedPiece
from vis.analyzers.indexers import interval, dissonance, metre, noterest, ngram, offset
from vis.analyzers.experimenters import frequency
from vis import workflow
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

# import matplotlib.pyplot as plt
# from scipy.cluster.hierarchy import dendrogram, linkage
# import numpy as np

# get the path to the 'vis' directory
import vis
VIS_PATH = vis.__path__[0]

pL = [
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

        # 'Morley_Duets/1 Goe yee my canzonets.xml',      # Morley Duos
        # 'Morley_Duets/2 When loe by break of morning.xml',
        # 'Morley_Duets/3 Sweet nymph.xml',
        # 'Morley_Duets/5 I goe before my darling.xml',
        # 'Morley_Duets/6 La Girandola.xml',
        # 'Morley_Duets/7 Miraculous loves wounding.xml',
        # 'Morley_Duets/8 Lo heere another love.xml',
        # 'Morley_Duets/11 Fyre and Lightning.xml',
        # 'Morley_Duets/13 Flora wilt thou torment mee.xml',
        # 'Morley_Duets/15 In nets of golden wyers.xml',
        # 'Morley_Duets/17 O thou that art so cruell.xml',
        # 'Morley_Duets/19 I should for griefe and anguish.xml',

        # 'Josquin_Duets/Agnus Dei.xml',                  # Josquin Duos
        # 'Josquin_Duets/Crucifixus.xml',
        # 'Josquin_Duets/Et incarnatus est.xml',
        # 'Josquin_Duets/Missa_Ad_Fugam_Sanctus_version_2_Benedictus.xml',
        # 'Josquin_Duets/Missa_Ad_fugam_Sanctus_version_2_Pleni.xml',
        # 'Josquin_Duets/Missa_Ad_fugam_Sanctus_version_2_Qui_venit.xml',
        # 'Josquin_Duets/Missa_Allez_regretz_I_Sanctus_Pleni.xml',
        # 'Josquin_Duets/Missa_Ave_maris_stella_Sanctus_Benedictus.xml',
        # 'Josquin_Duets/Missa_Ave_maris_stella_Sanctus_Qui_venit.xml',
        # 'Josquin_Duets/Missa_Pange_lingua_Sanctus_Benedictus.xml',
        # 'Josquin_Duets/Missa_Pange_lingua_Sanctus_Pleni_sunt_celi.xml',
        # 'Josquin_Duets/Qui edunt me.xml'
        ]

opera = float(len(pL))
f_setts = {'quarterLength': 2.0, 'method':'ffill'}
v_setts = {'quality': False, 'simple or compound': 'simple'}
h_setts = {'quality': False, 'horiz_attach_later': True, 'simple or compound': 'compound'}
n_setts = {'n': 2, 'horizontal': [('interval.HorizontalIntervalIndexer', '1')],
            'vertical': [('interval.IntervalIndexer', '0,1')], 'mark_singles': False}


class Cluster(object):

    def __init__(self):
        self.members = []
        self.piece_nums = []

    def get_members(self):
        return self.members

    def get_piece_nums(self):
        return self.piece_nums

    def get_count(self):
        return len(self.members)

    def add_members(self, source_clus):
        for p in source_clus:
            self.members.append(p)
            self.piece_nums.append(p.get_num())


class Piece(object):

    def __init__(self, data, number):
        self.data = data
        self.num = number

    def get_data(self):
        return self.data

    def get_num(self):
        return self.num

    def get_num_str(self):
        return str(self.num)


class HierClusterer(object):

    def __init__(self):
        self.clusters = []
        self.statuses = []
        self.history = []
        self.sers = []
        self.pair_comparisons = {}
        self.matrix = []

    def add_series(self, ser):
        self.sers.append(ser)

    def get_statuses(self):
        return self.statuses

    def get_history(self):
        return self.history

    def get_count(self):
        return len(self.clusters)

    def add_cluster(self, new_cluster):
        self.clusters.append(new_cluster)

    def remove_clusters(self, indecies):
        for c in indecies:
            del self.clusters[c]

    def merge(self, clusA, clusB):
        new_clus = Cluster()
        new_clus.add_members(clusA.get_members() + clusB.get_members())
        return new_clus

    def averageLinkage(self, clusA, clusB):
        all_sims = []
        for aPiece in clusA.get_members():
            for bPiece in clusB.get_members():
                if aPiece.get_num() < bPiece.get_num():
                    label = ','.join((aPiece.get_num_str(), bPiece.get_num_str()))
                else:
                    label = ','.join((bPiece.get_num_str(), aPiece.get_num_str()))
                all_sims.append(self.pair_comparisons[label])
        res = sum(all_sims)/float(len(all_sims))
        return res

    def advance(self, linkage_type):
        best_sim = 0
        best_match = (self.clusters[0], self.clusters[-1])
        best_indecies = (0, -1)
        for j, clusA in enumerate(self.clusters[:-1]):
            for k, clusB in enumerate(self.clusters[j+1:]):
                current = linkage_type(clusA, clusB)
                if current > best_sim:
                    best_sim = current
                    best_indecies = (j+k+1, j) # j has to be second to remove the right clusters

        best_match = (self.clusters[best_indecies[1]], self.clusters[best_indecies[0]])
        print 'Merged clusters were ' + str(round(best_sim, 2)) + '% similar.'
        new_cluster = self.merge(best_match[0], best_match[1])
        self.remove_clusters(best_indecies)
        self.add_cluster(new_cluster)
        #print best_indecies
        #best_merge = (self.clusters[best_indecies[1]].get_piece_nums(), self.clusters[best_indecies[0]].get_piece_nums())
        #self.history.append(best_merge)
        status = [clus.get_piece_nums() for clus in self.clusters]
        self.statuses.append(status)

    def populate_clusters(self, sers):
        for i, ser in enumerate(sers):
            new_p = Piece(ser, i+1)
            new_c = Cluster()
            new_c.add_members((new_p,))
            self.add_cluster(new_c)
        self.statuses.append([clus.get_piece_nums() for clus in self.clusters])

    def run_vis(self, pathnames, opera, f_setts, h_setts, v_setts, n_setts):
        t1 = time.time()
        sers = []

        for i, path in enumerate(pathnames):
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

                parts_nr.append(pd.Series(nr, index=part_index))

            basic_nr = pd.concat([s for s in parts_nr], axis=1)

            part_strings = []
            for num in part_numbers:
                part_strings.append(unicode(num))

            iterables = [['basic.NoteRestIndexer'], part_strings]
            basic_nr_multi_index = pd.MultiIndex.from_product(iterables, names = ['Indexer', 'Parts'])
            basic_nr.columns = basic_nr_multi_index

            filtered_notes = offset.FilterByOffsetIndexer(basic_nr, f_setts).run()

            horiz = interval.HorizontalIntervalIndexer(filtered_notes, h_setts).run()
            vert = interval.IntervalIndexer(filtered_notes, v_setts).run()

            comb_df = pd.concat([horiz, vert], axis=1)
            n_grams = ngram.NGramIndexer(comb_df, n_setts).run()
            ngram_freqs = frequency.FrequencyExperimenter(n_grams).run()[0]

            sers.append(ngram_freqs.iloc[:, 0])
            print 'N-gram analysis %d percent complete' % ((i+1)/opera*100) #Change %d to %f for float values

        t2 = time.time()
        print 'VIS Analysis took %f seconds.' % round((t2-t1), 2)
        return sers

    def pair_compare(self, sers):
        t1 = time.time()
        pair_comparisons = {}
        matrix = []
        numPieces = len(sers)
        comparisons = numPieces*(numPieces-1)/2.0
        count = 0
        for j, ser1 in enumerate(sers[:-1]):
            for k, ser2 in enumerate(sers[j+1:]):
                combined = ser1.add(ser2, fill_value=0)
                a_total = sum(ser1)
                b_total = sum(ser2)
                c_total = float(sum(combined))
                percA = a_total/c_total # out of 1, not out of 100
                percB = b_total/c_total
                similarity = 0.0
                count += 1
                for n in combined.index: # Each n is the name of an n-grams
                    a_ideal = combined.at[n] * percA
                    b_ideal = combined.at[n] * percB
                    a_val, b_val = 0, 0
                    if n in ser1.index:
                        a_val += ser1.at[n]
                    if n in ser2.index:
                        b_val += ser2.at[n]
                    a_acc = 1 - abs(a_val - a_ideal)/combined.at[n]
                    b_acc = 1 - abs(b_val - b_ideal)/combined.at[n]
                    n_perc = combined.at[n]/c_total
                    similarity += a_acc * b_acc * n_perc * 100
                pair_comparisons[','.join((str(j+1), str(j+k+2)))] = 100 - similarity
                matrix.append(100 - similarity)
            print '%d percent done with n-gram profile comparisons' % (count/comparisons*100)
        t2 = time.time()
        print 'Pair Comparisons took %f seconds.' % round((t2-t1), 2)
        self.pair_comparisons = pair_comparisons
        self.matrix = matrix

    def dendogram(self):

        plt.figure(1)
        plt.title("Lassus Duet Dissimilarities")

        linkage_matrix = linkage(dist_mat, 'average')

        dendrogram(linkage_matrix,
                   truncate_mode='lastp',
                   color_threshold=1,
                   show_leaf_counts=True)

        plt.show()

    def analyze(self, linkage_type):
        t1 = time.time()
        print 'Beginning Status: %s.' % (query.get_statuses()[-1],)
        print '--------'
        starting_count = query.get_count() - 1
        while query.get_count() > 1:
            query.advance(query.averageLinkage)
            print 'Clusters left: %d' % query.get_count()
            print 'Merge %d of %d complete.' % (len(query.statuses)-1, starting_count)
            print 'Status: %s.' % (query.get_statuses()[-1],)
            print '--------'
        t2 = time.time()
        print 'Final clustering step took %f seconds.' % round((t2-t1), 2)

query = HierClusterer()
sers = query.run_vis(pL, opera, f_setts, h_setts, v_setts, n_setts)
query.pair_compare(sers)
pdb.set_trace()

query.dendogram()
query.populate_clusters(sers)

query.analyze(query.averageLinkage)



pdb.set_trace()







