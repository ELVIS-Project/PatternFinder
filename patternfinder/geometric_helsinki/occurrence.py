import copy
import pdb

from pprint import pformat # for pretty __repr__
from patternfinder.base import BaseOccurrence

class GeometricHelsinkiOccurrence(BaseOccurrence):
    def __init__(self, generator, identifier, matching_pairs, score):
        self.pattern_notes = [vec.noteStart if vec.noteStart.derivation.origin is None
                else vec.noteStart.derivation.origin for vec in matching_pairs]
        self.source_notes = [vec.noteEnd if vec.noteEnd.derivation.origin is None
                else vec.noteEnd.derivation.origin for vec in matching_pairs]
        self.matching_pairs = matching_pairs

        super(GeometricHelsinkiOccurrence, self).__init__(
                generator, identifier, self.source_notes, score)

class Occurrence(object):
    def __init__(self, matching_pairs, score):
        self.matching_pairs = matching_pairs
        self.score = score

        # Each source note is either original or came from a chord, so 
        # we check the derivation to see which one to take. also, use 'is None'
        self.pattern_notes = [vec.noteStart if vec.noteStart.derivation.origin is None
                else vec.noteStart.derivation.origin for vec in matching_pairs]
        self.source_notes = [vec.noteEnd if vec.noteEnd.derivation.origin is None
                else vec.noteEnd.derivation.origin for vec in matching_pairs]

        #@TODO no measure info runs into errors? check for measure info!
        self.offset = self.source_notes[0].getOffsetInHierarchy(self.score)
        self.first_measure_num = self.source_notes[0].getContextByClass('Measure').number
        self.last_measure_num = self.source_notes[-1].getContextByClass('Measure').number
        self.measure_range = range(self.first_measure_num, self.last_measure_num + 1) # include last measure num

    def __repr__(self):
        return super(Occurrence, self).__repr__() + "\n" + pformat(self.matching_pairs)

    def __eq__(self, other):
        return self.matching_pairs == other.matching_pairs

    def __ne__(self, other):
        return self.matching_pairs == other.matching__pairs

    def get_excerpt(self, color='black'):
        """
        Returns a Score object representing the excerpt of the score which contains this occurrence
        You don't want to do this for all occurrences since deepcopy takes way too much time
        """
        excerpt = copy.deepcopy(self.score.measures(
                numberStart = self.first_measure_num,
                numberEnd = self.last_measure_num))
        for note in excerpt.flat.notes:
            if note.derivation.origin in self.source_notes:
                note.color = color

        # XML and Lily output don't seem to preserve the measure numbers
        # even though you can see them in stream.show('t')
        # Quick fix: put measure numbers in the excerpt title
        excerpt.metadata = music21.metadata.Metadata()
        exceprt.metadata.title = (" mm. {0} - {1}".format(self.first_measure_num, self.last_measure_num))
        return excerpt

    def color_in_source(self, c):
        for n in self.source_notes:
            n.color = c

        """
        Implementation:
        We look at the original source and gather all of the notes which have been matched.
        First we tag these matched notes them with a group. We use groups rather than id's because
        music21 will soon implement group-based style functions.
        Next, we deepcopy the measure range excerpt in the score corresponding to matched notes
        Finally we untag the matched notes in the original score and output the excerpt

        # Get a copied excerpt of the score
        first_measure_num = source_notes[0].getContextByClass('Measure').number
        last_measure_num = source_notes[-1].getContextByClass('Measure').number

        GET AN EXCERPT OF THE SCORE
        @TODO You don't want to do this for large searches, deepcopy takes way too much time
        if self.settings['excerpt']:
            result = copy.deepcopy(self.sourcePointSet.derivation.origin.measures(
                    numberStart = first_measure_num,
                    numberEnd = last_measure_num))
        else:
            result = copy.deepcopy(self.sourcePointSet.derivation.origin)

        # Untag the matched notes, process the occurrence
        for excerpt_note in result.flat.getElementsByGroup('occurrence'):
            excerpt_note.color = self.settings['colour']
            if self.settings['colour_source']:
                excerpt_note.derivation.origin.color = self.settings['colour']
            else:
                excerpt_note.derivation.origin.groups.remove('occurrence')

        # Output the occurrence
        if self.settings['show_pattern'] and self.patternPointSet.derivation.origin:
            # @TODO output the pattern from a pointset if that's the only input we have
            output = music21.stream.Opus(
                    [self.patternPointSet.derivation.origin, result])
        else:
            output = result

        output.metadata = music21.metadata.Metadata()
        output.metadata.title = (
                "Transposed by " + str(occ[0].diatonic.simpleNiceName) +
                # XML and Lily output don't seem to preserve the measure numbers
                # even though you can see them in .show('t')
                " mm. {0} - {1}".format(first_measure_num, last_measure_num))

        output.matching_pairs = occ

        #Save the pdf file as wtc-i-##_alg.pdf
        #temp_file = output.write('lily')
        # rename tmp.ly.pdf to file_name_base.pdf
        #os.rename(temp_file, ".".join(['output', 'pdf']))
        # rename tmp.ly to file_name_base.ly
        #os.rename(temp_file[:-4], ".".join(['output', 'ly']))

        return output
        """
