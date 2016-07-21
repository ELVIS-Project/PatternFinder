import cbrahmsGeo
import midiparser
import sys
import pprint

query = sys.argv[1]
source = sys.argv[2]

parsed_query = midiparser.run(query)
parsed_piece = midiparser.run(source)

exact_matches = cbrahmsGeo.P1(parsed_query, parsed_piece)

print(exact_matches)

