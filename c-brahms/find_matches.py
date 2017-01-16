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

def is_supported(music_file):
    """
    Returns true if :type: string 'music_file' is supported by music21
    """
    supported_formats = ['.krn', '.abc', '.mei', '.mscz', '.mid', '.midi', '.xml']
    return reduce(lambda x, y: x or y, map(lambda x: music_file.endswith(x), supported_formats))

### DEFINE OPTIONS
parser = OptionParser()
parser.add_option("-d", dest="directory", help="search for a query through all piece within directory", metavar="DIR")
#parser.add_option("-f", dest="file", help="search for a query in one file", metavar="FILE")
parser.add_option("-o", dest="option", help="provide optional settings to an algorithm", metavar="OPT")

### GET INPUT
# args[0] : algorithm name
# args[1] : query
# args[2] : source file (empty if directory flag has been used)
(parser_flags, args) = parser.parse_args()
ALGORITHM_NAME = args[0]
QUERY = args[1]

# Get algorithm function pointer and apply settings
ALGORITHM = partial(getattr(cbrahmsGeo, args[0]), option = parser_flags.option)

# Collect source files
if parser_flags.directory is None:
    SOURCES = [args[2]]
else:
    SOURCES = [parser_flags.directory + '/' + f for f in os.listdir(parser_flags.directory) if is_supported(f)]


### Print Introduction
# Check for empty flag (string concatenation will fail with NoneType)
if parser_flags.option is None:
    parser_flags.option = "default settings"

print("\n\n***** VIS-Ohrwurm *****"
        + "\nAlgorithm " + ALGORITHM_NAME + " is searching for " + QUERY + " in: " + str(SOURCES)
        + "\nWith option: " + parser_flags.option)

### FIND MATCHES
for source in SOURCES:
    print("\nFILE: " + source)

    # Parse query
    q_score = music21.converter.parse(QUERY)
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
    matches = tools.run_algorithm_with_midiparser(ALGORITHM, QUERY, source)

    # Skip this score if no matches were found
    if not matches:
        print("No matches found.")
        continue

    # Look for measure information
    if math.isnan(indexed_source[('metre.MeasureIndexer', '0')].loc[0]):
        print('No measure information. Here are a list of all matches (absolute offset, transposition):')
        pprint.pprint([str(m) for m in matches])
    else:
        print('Measure locator currently unreliable. Here are a list of all matches (absolute offset, transposition):')
        pprint.pprint([str(m) for m in matches])

        print('\nTrying to find measures...')
        for match in matches:
                mb = midiparser.get_measure_and_beat_from_onset(match.x, indexed_source)
                print('Pattern found at offset ' + str(mb[1]) + ' of measure ' + str(mb[0]) + ' (absolute offset: ' + str(match.x) + ' transposed by ' + str(match.y) + ' semitones).')


