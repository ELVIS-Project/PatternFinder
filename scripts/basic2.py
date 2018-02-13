import pdb
import music21
from patternfinder.geometric_helsinki.algorithms import GeometricHelsinkiBaseAlgorithm as algy
from patternfinder.geometric_helsinki.finder import Finder

p = music21.converter.parse('tinynotation: 4/4 c4 e4 d4')
s = music21.converter.parse('tinynotation: 4/4 c8 B8 e8 f8 d8')

my_algorithm = algy.factory(p, s, {'threshold' : 3, 'scale' : 1, 'algorithm': 'S2'})
my_finder = Finder(p, s, threshold=3, scale=1)

