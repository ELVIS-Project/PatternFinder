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


class Translation(TwoDVector):
    def __init__(self, line_seg, other_line_seg):
        self.line_seg = line_seg
        self.other_line_seg = other_line_seg
        super(Translation, self).__init__(other_line_seg.onset - line_seg.onset, other_line_seg.pitch - line_seg.pitch)

    def __cmp__(self, other_translation):
        return super(Translation, self).__cmp__(other_translation)

    def __repr__(self):
        return "Translation(line_seg={0}, other_line_seg={1})".format(str(self.line_seg), str(self.other_line_seg))


class TurningPoint(TwoDVector):

    def __init__(self, pattern_segment, source_segment, source_index, tp_type):
        distance_types = \
                [source_segment.onset - pattern_segment.offset, # type 0
                source_segment.onset - pattern_segment.onset, # type 1
                source_segment.offset - pattern_segment.offset, # type 2
                source_segment.offset - pattern_segment.onset] # type 3
        self.value = distance_types[tp_type]
        self.type = tp_type
        self.source_index = source_index
        self.pattern_segment = pattern_segment
        self.source_segment = source_segment
        super(TurningPoint, self).__init__(self.value, source_segment.pitch - pattern_segment.pitch)

    def __cmp__(self, other_turning_point):
        return super(TurningPoint, self).__cmp__(other_turning_point)

    def __repr__(self):
        return "TurningPoint(pattern_segment={0}, source_segment={1}, source_index={2}, tp_type={3}): vector={4}".format(str(self.pattern_segment), str(self.source_segment), self.source_index, self.type, self.vector())

class LineSegment(TwoDVector):

#    def __init__(self, onset, pitch, offset = None, duration = None):
    def __init__(self, data):
        self.data = data
        self.onset, self.duration, self.pitch = data
        self.offset = self.onset + self.duration
        self.turning_point = []
        super(LineSegment, self).__init__(self.onset, self.pitch)
#        self.onset = onset
#        self.pitch = pitch
#        self.offset = offset
#        self.duration = duration

    def __add__(self, translation):
        """
        Built-in add function to support translating line segments by a Translation object
        Input is :type: Translation
        Output is :type: LineSegment, having been shfited in two dimensions by Translation
        """
        new_segment = LineSegment(self.data)
        new_segment.onset += translation.x
        new_segment.x += translation.x
        new_segment.offset += translation.x
        new_segment.pitch += translation.y
        new_segment.y += translation.y
        return new_segment

    def __sub__(self, other_line_segment):
        """
        Built-in subtract function to support computing a Translation which can translate one LineSegment onto another.
        Input is :type: LineSegment
        Output is :type: Translation, such that self + Translation = LineSegment
        """
        #return Translation(self, other_line_segment)
        return TwoDVector(self.onset - other_line_segment.onset, self.pitch - other_line_segment.pitch)

    def __cmp__(self, other_line_segment):
        return super(LineSegment, self).__cmp__(other_line_segment)

    def __str__(self):
        return "onset {0}, duration {1}, pitch {2}".format(self.onset, self.duration, self.pitch)
    def __repr__(self):
        return "LineSegment(onset={0}, offset={1}, duration={2}, pitch={3})".format(self.onset, self.offset, self.duration, self.pitch)


class LineSegmentSet():

    def __init__(self, data):
        self.data = data
        self.onsets, self.offsets, self.durations, self.notes = zip(*data)

    def onsets_with_notes(self):
        return zip(self.onsets, self.notes)
    def offsets_with_notes(self):
        return zip(self.offsets, self.notes)
