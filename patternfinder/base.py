import music21
import copy
import pprint

class BaseOccurrence(music21.base.Music21Object):

    def __init__(self, generator, identifier, list_of_notes, score):
        start_offset, end_offset = (list_of_notes[0].getOffsetInHierarchy(score),
                list_of_notes[-1].getOffsetInHierarchy(score))

        # Init music21 object with an unpacked dictionary rather than kwargs
        # since 'id' is a reserved python keyword
        super(BaseOccurrence, self).__init__(**{
            'id' : identifier,
            'groups' : [],
            'duration' : music21.duration.Duration(end_offset - start_offset),
            # 'activeSite' : score, # can't set object active site to somewhere it does not belong
            'offset' : start_offset,
            'priority' : 0,
            # Will sites be computed automatically if I leave it out? There may be more contexts other than score
            'sites' : score,
            'derivation' : music21.derivation.Derivation()})
            # Music21 doesn't have style or Editorial() attributes - incorrect documentation?
            # 'style' : music21.style.Style(), 
            #'editorial' : music21.editorial.Editorial()})

        self.derivation.method = generator
        self.derivation.origin = score
        self.notes = list_of_notes
        self.score = score

    def __repr__(self):
        return pprint.pformat(self.notes)

    def __eq__(self, other):
        return self.notes == other.notes

    def __ne__(self, other):
        return self.notes != other.notes

    def get_excerpt(self, left_padding=0, right_padding=0):
        """
        Returns a Score object representing the excerpt of the score which contains this occurrence
        All notes in the score which form part of the occurrence will belong to the 'occurrence' group

        You don't want to do this for all occurrences since deepcopy takes way too much time. That's
        why we put this in a separate method rather than __init__

        Input
        -------
        self - Occurrence object with notes and an associated score
        left_padding - an integer number of measures to include to the excerpt on the left side
        right_padding - an integer number of measures to include to the excerpt on the right side

        Raises
        -------
        StreamException if self.score has no measure information for the first or last notes
        """
        # beatAndMeasureFromOffset() will raise a StreamException if self.score has no measure info
        _beat, start_measure = self.score.beatAndMeasureFromOffset(self.offset)
        _beat, end_measure = self.score.beatAndMeasureFromOffset(self.offset + self.duration.quarterLength)

        # Get a deepcopy excerpt of the score so post-processing will not modify original score
        excerpt = copy.deepcopy(self.score.measures(
                numberStart = start_measure.number - left_padding,
                numberEnd = end_measure.number + right_padding))

        # Tag the occurrence notes in the excerpt
        for note in excerpt.flat.notes:
            if note.derivation.origin in self.source_notes:
                note.groups.append('occurrence')

        # @TODO
        # XML and Lily output don't seem to preserve the measure numbers
        # even though you can see them in stream.show('t')
        # Quick fix: put measure numbers in the excerpt title
        excerpt.metadata = music21.metadata.Metadata()
        excerpt.metadata.title = (" mm. {0} - {1}".format(
            start_measure.number, end_measure.number))

        return excerpt
