import cbrahmsGeo
import midiparser
import sys
import pprint

#if len(sys.argv) > 2:
#query = sys.argv[1]
#source = sys.argv[2]

#parsed_query = midiparser.run(query)
#parsed_piece = midiparser.run(source)

parsed_query = [[0, 64], [2, 65], [4, 70]]
parsed_piece = midiparser.run('music_files/matona.mid')

exact_matches = cbrahmsGeo.P1(parsed_query, parsed_piece)

print(exact_matches)

