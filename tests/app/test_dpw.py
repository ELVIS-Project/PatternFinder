import sys
sys.path.insert(0, '/home/dgarfinkle/PatternFinder')

import music21
from app import dpw2

def test_dpw():
    source = music21.converter.parse('tinynotation: c4 e4 g4')
    pattern = music21.converter.parse('tinynotation: c4 e4')

    M = dpw2.algorithm(pattern, source)

    print(M)

    assert False
