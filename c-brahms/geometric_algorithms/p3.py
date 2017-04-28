from LineSegment import TwoDVector, LineSegment, LineSegmentSet, TurningPoint, TwoDVector, Bucket
from Queue import PriorityQueue
import music21
import itertools
import geoAlgorithm
import NoteSegment
import music21
import pdb

class P3(geoAlgorithm.P):

    def pre_process(self):
        super(P3, self).pre_process()
        if self.settings['threshold'] == 'all':
            pass

    def process_results(self):
        return [(r.x, r.y) for r in self.results]

    def post_process(self):
        pass

    def algorithm(self):
        """
        Input: two lists of horizontal line segments. One is the 'pattern', which we are looking for in the larger 'source'
        Output: all shifts which result in the largest intersection (measured in length) between the two sets of line segments

        Only checks for transpositions within -127 and 127 semitones.
        """
        #curiosities: Not sure a negative (leftwards) match is possible with this algorithm (i.e., just a suffix of the pattern matches the beginning of the source). think about it?
        # Sanity check: Each bucket represents a SLOPE and a TALLY for every y value. 
        # There are four turning points per pattern segment. Each pattern segment can influence the n tally (there are as many tallys as there are vertical translations) in four ways! We sort them all and go through it one at a time.
        source = self.source_line_segments
        pattern = self.pattern_line_segments

        # Sort pattern and source
        #pattern = LineSegmentSet(pattern)
        source = LineSegmentSet(source)
        #pattern.onset_sort = sorted(pattern)

        # Remove overlapping of segments
        if self.settings['overlap']:
            pass
        else:
            # Merging overlaps depends on previously being sorted.
            source.mergeOverlappingSegments()
            source.mergeOverlappingSegments()

        pattern.sort()
        source_onset_sort = sorted(source, key = lambda x: (x.onset, x.pitch))
        source_offset_sort = sorted(source, key = lambda x: (x.offset, x.pitch))

            #helper = source_onset_sort[1:]
            #source_onset_sort.append(None)
            #source_no_overlap = [mergeTwoSegments(elt[0], elt[1]) if elt[0].doesOverlapWith(elt[1]) else elt[0] for elt in zip(source_onset_sort, helper)]


        # All vertical translations are between -127 and 127 since there are 127 possible MIDI values.
        # So, we need a total of (127*2 + 1) = 255 buckets to keep track of each C_h.
        # Negative indices will wrap around. 
        # Initial prev_tp does not matter since slope is zero
        C_h = [Bucket(value=0, slope=0, prev_tp=TwoDVector(0, 0)) for i in range(256)]

        # Store 4 * m turning points in a priority queue (4 types per pattern segment)
        turning_points = PriorityQueue(4 * len(pattern))
        for p in pattern:
            turning_points.put(TurningPoint(p, source_onset_sort[0], 0, 0))
            turning_points.put(TurningPoint(p, source_onset_sort[0], 0, 1))
            turning_points.put(TurningPoint(p, source_offset_sort[0], 0, 2))
            turning_points.put(TurningPoint(p, source_offset_sort[0], 0, 3))

        # Keep track of the longest intersection
        best = 0
        list_of_shifts = []
        result_stream = music21.stream.Stream()

        # LOOP: All 4 * m turning points now traverse the source. types 0,1 traverse onsets, and types 2,3 traverse offsets.
        for i in range(4 * len(pattern) * len(source)):
            min_tp = turning_points.get()
            # min_tp.y is a whole number (MIDI pitch) so we can cast it to an int
            i = int(min_tp.y)

            # Each Turning Point changes the SLOPE of the total intersection: a turning point dictates the behaviour of the score up to the next Turning Point. So every time we take out a new turning point from the priority queue, the first thing we have to do is update the score.
            # Update total intersection value
            if min_tp.x != C_h[i].prev_tp.x:
                C_h[i].value += C_h[i].slope * (min_tp.x - C_h[i].prev_tp.x)

            # Keep track of best matches
            if C_h[i].value > best: # New record!
                list_of_shifts = [] # Reset list of accepted translations
                best = C_h[i].value
            # Append a translation if it hasn't been added already
            if C_h[i].value >= best and min_tp not in list_of_shifts:
                list_of_shifts.append(min_tp)

            # Update slope
            if min_tp.type in [0, 3]:
                C_h[i].slope += 1
            else:
                C_h[i].slope += -1

            # Save current turning point so other TP's know long it has been since the value has been updated
            C_h[i].prev_tp = min_tp
            # Find next turning point of this type (move pointer forward)
            if min_tp.source_index < len(source) - 1:
                if min_tp.type == 0 or min_tp.type == 1:
                    turning_points.put(TurningPoint(min_tp.pattern_segment, source_onset_sort[min_tp.source_index + 1], min_tp.source_index + 1, min_tp.type))
                else: # type == 2 or 3
                    turning_points.put(TurningPoint(min_tp.pattern_segment, source_offset_sort[min_tp.source_index + 1], min_tp.source_index + 1, min_tp.type))

        return list_of_shifts

