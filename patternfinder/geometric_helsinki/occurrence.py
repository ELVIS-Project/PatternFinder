import copy
import pdb

from pprint import pformat # for pretty __repr__
from patternfinder.base import BaseOccurrence

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

