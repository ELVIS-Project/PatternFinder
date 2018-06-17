import copy
import pdb

from pprint import pformat # for pretty __repr__
from patternfinder.base import BaseOccurrence
from patternfinder.geometric_helsinki.geometric_notes import NotePointSet

class GeometricHelsinkiOccurrence(BaseOccurrence):
    def __init__(self, generator, identifier, matching_pairs, score, pointset):
        #self.pattern_notes = [vec.noteStart.original_note for vec in matching_pairs]
        #self.source_notes = [vec.noteEnd.original_note for vec in matching_pairs]
        self.source_notes = [score.flat.getElementById(vec.noteEnd.original_note_id)
                for vec in matching_pairs]

        self.matching_pairs = matching_pairs

        # Convert pointset into a list of music21 ids
        pointset_ids = [n.id for n in list(pointset.flat.notes)]
        # Get the indices of the source note occurrences in the sorted point set
        source_indices = [pointset_ids.index(vec.noteEnd.id) for vec in matching_pairs]
        # Find the biggest gap between two source notes
        self.max_window = max((y-x) for x, y in zip(source_indices[:-1], source_indices[1:]))

        super(GeometricHelsinkiOccurrence, self).__init__(
                generator, identifier, self.source_notes, score)

    def color_source_notes(self, c):
        for note in self.source_notes:
            note.color = c


def get_excerpt_from_note_list(mass_path, note_list, color='red'):
    score = music21.converter.parse(mass_path)
    pointset = list(NotePointSet(score).flat.notes)

    pointset_indices = [int(i) for i in note_indices.split(',')]
    score_note_ids = [pointset[i].original_note_id for i in pointset_indices]

    _, start_measure = score.beatAndMeasureFromOffset(pointset[pointset_indices[0]].offset)
    _, end_measure = score.beatAndMeasureFromOffset(pointset[pointset_indices[-1]].offset + pointset[-1].duration.quarterLength - 1)

    excerpt = score.measures(numberStart=start_measure.number, numberEnd=end_measure.number)
    for note in excerpt.flat.notes:
        if note.id in score_note_ids:
            note.style.color = color

    sx = music21.musicxml.m21ToXml.ScoreExporter(excerpt)
    musicxml = sx.parse()

    from io import StringIO
    import sys
    bfr = StringIO()
    sys.stdout = bfr
    sx.dump(musicxml)
    output = bfr.getvalue()
    sys.stdout = sys.__stdout__

    return output
