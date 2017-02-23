import itertools
from collections import namedtuple

Point = namedtuple('Point', ['x', 'y'])

class TwoDVector(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vector = lambda: [self.x, self.y]

    def __cmp__(self, other_vector):
        if self.vector() < other_vector.vector():
            return -1
        elif self.vector() > other_vector.vector():
            return 1
        return 0

    def __str__(self):
        return "{0}".format(str(self.vector()))
    def __repr__(self):
        return "TwoDVector(x={0}, y={1})".format(str(self.x), str(self.y))

class TurningPoint(TwoDVector):

    def __init__(self, pattern_segment, source_segment, source_index, tp_type):
        v = -99999
        if tp_type == 0:
            v = source_segment.onset - pattern_segment.offset
        elif tp_type == 1:
            v = source_segment.onset - pattern_segment.onset
        elif tp_type == 2:
            v = source_segment.offset - pattern_segment.offset
        elif tp_type == 3:
            v = source_segment.offset - pattern_segment.onset

        self.type = tp_type
        self.source_index = source_index
        self.pattern_segment = pattern_segment
        self.source_segment = source_segment
        super(TurningPoint, self).__init__(v, source_segment.pitch - pattern_segment.pitch)

        # Update the TP pointer of the given pattern segment
        pattern_segment.turning_points = self

    def next(self, source_list):
        if self.source_index < len(source_list) - 1:
            self.source_segment = source_list[source_index + 1]
            self.source_index += 1
        return self

    def __cmp__(self, other_turning_point):
        return super(TurningPoint, self).__cmp__(other_turning_point)

    def __repr__(self):
        return "TurningPoint(pattern_segment={0}, source_segment={1}, source_index={2}, tp_type={3}): vector={4}".format(str(self.pattern_segment), str(self.source_segment), self.source_index, self.type, self.vector())

class Bucket():
    def __init__(self, value, slope, prev_tp):
        self.value = value
        self.slope = slope
        self.prev_tp = prev_tp

class LineSegment(TwoDVector):
    #TODO should be able to just add 4 to .x or .onset and everything updates

    def __init__(self, onset, pitch, duration = 0):
#    def __init__(self, data):
        self.onset = onset
        self.pitch = pitch
        self.duration = duration
        self.update()
#        self.turning_point = []

    def __add__(self, t):
        # TODO should be able to just add 2-tuples without making them TwoDVectors
        """
        Custom add function to shift line segments
        Input is :type: TwoDVector
        Output is :type: LineSegment, which corresponds to 'self' having been shfited in two dimensions by a TwoDVector
        """
        new_segment = LineSegment(self.onset + t.x, self.pitch + t.y, self.duration)
        return new_segment

    def __sub__(self, other_line_segment):
        """
        Custom subtract function to calculate the shift difference between line segments
        Input is :type: TwoDVector
        Output is :type: TwoDVector, such that self + TwoDVector = other_line_segment
        """
        return TwoDVector(self.onset - other_line_segment.onset, self.pitch - other_line_segment.pitch)

    def __mul__(self, factor):
        """
        Custom mult to stretch or shrink the duration of a LineSegment
        Expects a scalar value.
        """
        return LineSegment(self.onset, self.pitch, self.duration * factor)

    def __div__(self, factor):
        """
        Custom div to stretch or shrink the duration of a LineSegment. Calls __mul__ with reciprocal
        Expects a scalar value.
        """
        return self.__mul__(self, 1 / factor)

    def __cmp__(self, other_line_segment):
        return super(LineSegment, self).__cmp__(other_line_segment)

    def __str__(self):
        return "onset {0}, duration {1}, pitch {2}".format(self.onset, self.duration, self.pitch)
    def __repr__(self):
        return "LineSegment(onset={0}, offset={1}, duration={2}, pitch={3})".format(self.onset, self.offset, self.duration, self.pitch)

    def update(self):
        # update the offset
        self.offset = self.onset + self.duration
        # update x, y attributes of the namedtuple superclass
        super(LineSegment, self).__init__(self.onset, self.pitch)


    def doesOverlapWith(self, other_line_segment):
        """
        Checks if two line segments overlap
        'Overlap' between two segments is defined as a non-empty intersection in a 2-d plane
        """
        # Check for identical pitch
        if self.pitch != other_line_segment.pitch:
            return False
        # Renumber line segments so that 'self' is the first occuring one
        elif self.onset > other_line_segment.onset:
            return other_line_segment.doesOverlapWith(self)
        # Check if 'self' sustains over 'other'
        else:
            return self.offset > other_line_segment.onset

    def mergeWith(self, other_line_segment):
        """
        Merges two overlapping line segments
        Does not check if the line segments are overlapping nor does it raise an exception if this is not the case. Overlap should be confirmed before calling this function!
        """
        return LineSegment(self.onset, self.pitch, other_line_segment.offset - self.onset)

class LineSegmentSet(list):

    def mergeOverlappingSegments(self):
        """
        Merges all overlapping Segments in the Set
        Not strictly pythonic... Could improve by:
            1) sorting the list by pitch and then onset
            2) zip it with itself offset by 1, map .doesOverlapWith, use groupby() and fold .mergeWith on the partitions
        """
#        helper = zip(self, self[1:])
#        map(lambda h: h[0].doesOverlapWith(h[1])
#        then, partition the set with groupby() and use fold on the partitions
#        new = [[la for x in la] for elt in self]

#        for i in range(len(self[:-1])):
#            while (i < len(self) - 1) and self[i].doesOverlapWith(self[i+1]):
#                self[i] = self[i].mergeWith(self.pop(i+1))

        m = len(self)
        for i in range(m):
            j = i + 1
            while j < m:
                if self[i].doesOverlapWith(self[j]):
                    self[i] = self[i].mergeWith(self.pop(j))
                    m -= 1
                j += 1

#    def mergeOverlappingSegmentsNew(self):
#        self.sort(key = lambda x: (x.pitch, x.onset))
#        overlaps = [(e[0], e[1], e[0].doesOverlapWith[1]) for e in zip(self, self[1:])]
        # Doesn't work cause it appends groups with 'False' also
#        return [reduce(lambda l, r: l[0].mergeWith(r[0]), g) for g in groupby(overlaps, lambda x: x[2])]

    def onsets_with_notes(self):
        return zip(self.onsets, self.notes)
    def offsets_with_notes(self):
        return zip(self.offsets, self.notes)
