import music21
from app.dpw2 import *

target = music21.converter.parse('tinynotation: c4 e4 g4')
pattern = music21.converter.parse('tinynotation: c4 e4')

pattern = sorted(list(pattern.flat.notes), key=lambda n: (n.offset, chrpitch(n)))
target = sorted(list(target.flat.notes), key=lambda n: (n.offset, chrpitch(n)))
window = len(target)

M = init_matrix(pattern, target, window)
