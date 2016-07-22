from vis.analyzers.indexers import noterest, metre
import music21
import pandas # to concatenate dataframes
import cbrahmsGeo
import midiparser
import math # to check for float('nan')
import sys # to get command line arguments
import pprint # for pretty printing results
import pdb

query = sys.argv[1]
source = sys.argv[2]

q_score = music21.converter.parse(query)
indexed_query = pandas.concat([
    noterest.NoteRestIndexer(q_score).run(),
    metre.DurationIndexer(q_score).run()], axis = 1).ffill()

s_score = music21.converter.parse(source)
indexed_source = pandas.concat([
    noterest.NoteRestIndexer(s_score).run(),
    metre.DurationIndexer(s_score).run(),
    metre.MeasureIndexer(s_score).run()], axis = 1).ffill()

parsed_query = midiparser.run(indexed_query)
parsed_piece = midiparser.run(indexed_source)

exact_matches = cbrahmsGeo.P1(parsed_query, parsed_piece)

if math.isnan(indexed_source[('metre.MeasureIndexer', '0')].loc[0]):
        print('No measure information. Here are a list of all exact matches (absolute offset, transposition):')
        pprint.pprint(exact_matches)
else:
    for match in exact_matches:
            mb = midiparser.get_measure_and_beat_from_onset(match[0], indexed_source)
            print('Pattern found at offset ' + str(mb[1]) + ' of measure ' + str(mb[0]) + ' (absolute offset: ' + str(match[0]) + ' transposed by ' + str(match[1]) + ' semitones).')


