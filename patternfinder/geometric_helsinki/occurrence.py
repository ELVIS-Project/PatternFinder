import copy
import pdb

from pprint import pformat # for pretty __repr__
from patternfinder.base import BaseOccurrence

class GeometricHelsinkiOccurrence(BaseOccurrence):
    def __init__(self, generator, identifier, matching_pairs, score):
        #self.pattern_notes = [vec.noteStart.original_note for vec in matching_pairs]
        #self.source_notes = [vec.noteEnd.original_note for vec in matching_pairs]
        self.source_notes = [score.flat.getElementById(vec.noteEnd.original_note_id)
                for vec in matching_pairs]

        self.matching_pairs = matching_pairs

        super(GeometricHelsinkiOccurrence, self).__init__(
                generator, identifier, self.source_notes, score)
