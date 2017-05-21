from LineSegment import TwoDVector, LineSegment, LineSegmentSet, TurningPoint, TwoDVector, Bucket
from Queue import PriorityQueue
from NoteSegment import CmpItQueue, NotePointSet, InterNoteVector
from collections import namedtuple # container to hold sum of line segment intersection
from more_itertools import peekable # for peekable InterNoteVector generators
import music21
import itertools
import geo_algorithms
import NoteSegment
import copy
import pdb

class P3(geo_algorithms.P):

    def pre_process(self):
        super(P3, self).pre_process()
        self.sourcePointSet_offsetSort = NotePointSet(self.source, offsetSort=True)
        #TODO merge overlapping notes using stream.getOverlaps()


    def process_result(self, result):
        # TODO insert sort (using bisect_insort) vectors to matching_pairs rather than sorting them after
        return sorted(result['matching_pairs'], key=lambda x: x.noteStartIndex)

    def filter_result(self, result):
        total_pattern_value = sum(map(lambda x: x.duration.quarterLength, self.patternPointSet))
        return (result['value'] >= self.settings['%threshold'] * total_pattern_value)

    def algorithm(self):
        pattern = self.patternPointSet
        source_onsetSort = self.sourcePointSet
        source_offsetSort = self.sourcePointSet_offsetSort
        settings = self.settings

        shifts = CmpItQueue(lambda x: (x.peek(),), 4 * len(pattern))
        bucket = namedtuple('bucket', ['value', 'slope', 'active_tps'])
        score_buckets = {}

        for note in pattern:
            # Push four inter vectors generators for each pattern note, with varying tp_types (0, 1, 2, 3)
            # tp_types 0, 1 iterate through a source sorted by onset (attack)
            # while types 2, 3 iterate through a source sorted by offset (release)
            shifts.put(peekable((lambda p: (InterNoteVector(p, pattern, s, source_onsetSort, tp_type=0) for s in source_onsetSort))(note)))
            shifts.put(peekable((lambda p: (InterNoteVector(p, pattern, s, source_onsetSort, tp_type=1) for s in source_onsetSort))(note)))
            shifts.put(peekable((lambda p: (InterNoteVector(p, pattern, s, source_offsetSort, tp_type=2) for s in source_offsetSort))(note)))
            shifts.put(peekable((lambda p: (InterNoteVector(p, pattern, s, source_offsetSort, tp_type=3) for s in source_offsetSort))(note)))

        for turning_point_generator in shifts:
            inter_vec = turning_point_generator.next()

            # Get the current bucket, or initialize it
            cur_bucket = score_buckets.setdefault(inter_vec.y, {'value' : 0, 'last_value': 0, 'slope' : 0, 'prev_tp' : None, 'matching_pairs' : []})

            # Each turning point dictates the behaviour (slope) of the score up until the next turning point. So the very first thing we need to do is update the score (especially before updating the slope!)
            cur_bucket['value'] += cur_bucket['slope'] * (inter_vec.x - cur_bucket['prev_tp'].x) if cur_bucket['prev_tp'] else 0

            # Update the slope after we update the value
            cur_bucket['slope'] += 1 if inter_vec.tp_type in [0,3] else -1
            # Save current turning point so other TP's know long it has been since the value has been updated
            cur_bucket['prev_tp'] = inter_vec

            # Keep track of the matching pairs
            if inter_vec.tp_type == 0:
                cur_bucket['matching_pairs'].append(inter_vec)
            elif inter_vec.tp_type == 3:
                cur_bucket['matching_pairs'].remove(
                        InterNoteVector(inter_vec.noteStart, inter_vec.noteStartSite, inter_vec.noteEnd, inter_vec.noteEndSite, 0))

            # Only return occurrences if the intersection is increasing (necessarily must return non-zero intersections since 'last_value' starts at 0
            if cur_bucket['value'] > cur_bucket['last_value']:
                yield cur_bucket
                cur_bucket['last_value'] = cur_bucket['value']

            # The PQ will try to peek() the generator; if it has been exhausted, then don't put it back in!
            try:
                shifts.put(turning_point_generator)
            except StopIteration:
                pass

    def algorithmOld(self):
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

