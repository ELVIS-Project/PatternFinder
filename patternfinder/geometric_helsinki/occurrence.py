import copy
import pdb
from pprint import pformat # for pretty __repr__

class Occurrence(object):
    def __init__(self, matching_pairs):
        self.matching_pairs = matching_pairs
        # Each source note is either original or came from a chord, so 
        # we check the derivation to see which one to take. also, use 'is None'
        self.pattern_notes = [vec.noteStart if vec.noteStart.derivation.origin is None
                else vec.noteStart.derivation.origin for vec in matching_pairs]
        self.source_notes = [vec.noteEnd if vec.noteEnd.derivation.origin is None
                else vec.noteEnd.derivation.origin for vec in matching_pairs]
        self.first_measure_num = self.source_notes[0].getContextByClass('Measure').number
        self.last_measure_num = self.source_notes[-1].getContextByClass('Measure').number


    def __repr__(self):
        return super(Occurrence, self).__repr__() + "\n" + pformat(self.matching_pairs)


    def get_excerpt(self):
        """
        Returns a Score object representing the excerpt of the score which contains this occurrence
        You don't want to do this for all occurrences since deepcopy takes way too much time
        """
        excerpt = self.source_notes[0].activeSite.derivation.origin.measures(
                numberStart = self.first_measure_num,
                numberEnd = self.last_measure_num)
        return excerpt

    def color_in(self, c, score):
        for n in getattr(self, score + "_notes"):
            n.color = c

        """
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
