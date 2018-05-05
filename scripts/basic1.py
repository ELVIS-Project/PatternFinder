import music21
from patternfinder import geometric_helsinki

PALESTRINA_KYRIE_PATH = 'music_files/lupi/palestrina/Je_suis_desheritee_Kyrie.xml'
lupi_chanson = music21.converter.parse('music_files/lupi/Je_suys_desheritee.xml')
#A1 = music21.converter.parse('music_files/lupi/module_A1.xml')

module_A1 = music21.stream.Stream(
        (lupi_chanson.parts['Bass'].measures(1,3), lupi_chanson.parts['Tenor'].measures(1,3)))
module_A1.id = 'module_A1'

"""
INIT THEN USE UPDATE
"""
my_finder = geometric_helsinki.Finder()
my_finder.update(
        pattern=module_A1,
        threshold=0.9,
        scale='warped',
        pattern_window=3,
        source_window=5)

my_finder.update(source=PALESTRINA_KYRIE_PATH)
for occ in my_finder:
    occ.get_excerpt('red').write('lily.png')

"""
INIT FINDER WITH SCORES
my_finder = helsinki.Finder(module_A1, PALESTRINA_KYRIE_PATH,
        threshold=0.8,
        scale='warped',
        pattern_window=3,
        source_window=5)
"""

occurrences = list(my_finder)
#output = occurrences[0].get_excerpt('red').write('lily.png')

