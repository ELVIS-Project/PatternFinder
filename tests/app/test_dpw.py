import sys
# TODO figure out how to do proper python imports:
sys.path.insert(0, '/home/dgarfinkle/PatternFinder')

import music21
from webapp import dpwc

def test_dpw():
    source = music21.converter.parse('tinynotation: c4 e4 g4')
    pattern = music21.converter.parse('tinynotation: c4 e4')

    M = dpw2.algorithm(pattern, source)

    print(M)

    assert False
