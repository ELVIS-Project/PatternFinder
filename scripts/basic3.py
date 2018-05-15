import music21

from patternfinder.geometric_helsinki import Finder

p = music21.converter.parse('tinynotation: 4/4 c4 e4 g4')
s = music21.converter.parse('tinynotation: 4/4 d4 f#4 a4')

my_finder = Finder(p, s)

p = music21.converter.parse('tinynotation: 4/4 c4 e4 g4')
s = music21.converter.parse('tinynotation: 4/4 d4 f#4 g4 a4')
my_warped = Finder(p, s, scale='warped')
