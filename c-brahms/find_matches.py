from vis.analyzers.indexers import noterest, metre
from tests import tools
from functools import partial
import music21
import pandas # to concatenate dataframes
import cbrahmsGeo
import midiparser
import math # to check for float('nan')
import sys # to get command line arguments
import pprint # for pretty printing results
import pdb
import os
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-d", dest="directory", help="search for a query through all piece within directory", metavar="DIR")
#parser.add_option("-f", dest="file", help="search for a query in one file", metavar="FILE")
parser.add_option("-o", dest="option", help="provide optional settings to an algorithm", metavar="OPT")
(options, args) = parser.parse_args()

def is_supported(music_file):
    """
    Returns true if :type: string 'music_file' is supported by music21
    """
    supported_formats = ['.krn', '.abc', '.mei', '.mscz', '.mid', '.midi'] # bach_BWV2_chorale.xml was not working yesterday. will investigate further
    return reduce(lambda x, y: x or y, map(lambda x: music_file.endswith(x), supported_formats))

algorithm_string = args[0]
query = args[2]
# Add all source files to search through
sources = []
if options.directory is not None:
    for f in os.listdir(options.directory):
        if is_supported(f):
            sources.append(options.directory + '/' + f)
else:
    sources.append(args[1])


print("\n\n***** VIS-Ohrwurm *****\n")
print("Algorithm " + algorithm_string + " is searching for " + query + " in: " + str(sources))
if options.option is not None:
    print("With option " + options.option)
algorithm = partial(getattr(cbrahmsGeo, algorithm_string), option = options.option)

for source in sources:
    print("\nFILE: " + source)

    # Parse query
    q_score = music21.converter.parse(query)
    indexed_query = pandas.concat([
        noterest.NoteRestIndexer(q_score).run(),
        metre.DurationIndexer(q_score).run()], axis = 1).ffill()

    # Parse score
    s_score = music21.converter.parse(source)
    indexed_source = pandas.concat([
        noterest.NoteRestIndexer(s_score).run(),
        metre.DurationIndexer(s_score).run(),
        metre.MeasureIndexer(s_score).run()], axis = 1).ffill()

    parsed_query = midiparser.run(indexed_query)
    parsed_piece = midiparser.run(indexed_source)

    # Search for query in score
    matches = tools.run_algorithm_with_midiparser(algorithm, query, source)

    # Skip this score if no matches were found
    if not matches:
        print("No matches found.")
        continue

    # Look for measure information
    if math.isnan(indexed_source[('metre.MeasureIndexer', '0')].loc[0]):
            print('No measure information. Here are a list of all matches (absolute offset, transposition):')
            pprint.pprint([str(m) for m in matches])
    else:
        for match in matches:
                mb = midiparser.get_measure_and_beat_from_onset(match[0], indexed_source)
                print('Pattern found at offset ' + str(mb[1]) + ' of measure ' + str(mb[0]) + ' (absolute offset: ' + str(match[0]) + ' transposed by ' + str(match[1]) + ' semitones).')


