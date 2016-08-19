class 2DVector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vector = [x, y]

    def __cmp__(self, vector, other_vector):
        if self.vector < other_vector.vector
            return -1
        elif self.vector > other_vector.vector:
            return 1
        return 0


class Translation(2DVector):
    def __init__(self, line_seg, other_line_seg):
        super().__init__(other_line_seg.onset - line_seg.onset, other_line_seg.offset - line_seg.offset)

    def __cmp__(self, other_translation):
        super().__cmp__(self, other_translation)


class TurningPoint(Translation):
    def __init__(self, pattern_segment, source_segment, source_index, tp_type):
        super().__init__(pattern_segment, source_segment)
        self.type = tp_type
        self.source_index = source_index

        if self.type == 1:
            self.x = source_segment.onset - pattern_segment.offset
        elif self.type == 2:
            self.x = source_segment.onset - pattern_segment.onset
        elif self.type == 3:
            self.x = source_segment.offset - pattern_segment.offset
        elif self.type == 4:
            self.x = source_segment.offset - pattern_segment.onset

    def __cmp__(self, other_turning_point):
        super().__cmp__(self, other_turning_point)


class LineSegment:

    def __init__(self, onset, offset, duration, pitch):
        self.onset = onset
        self.offset = offset
        self.duration = duration
        self.pitch = pitch

    def __add__(self, translation):
        """
        Built-in add function to support translating line segments by a Translation object
        Input is :type: Translation
        Output is :type: LineSegment, having been shfited in two dimensions by Translation
        """
        return LineSegment(self.onset + translation.x, self.offset + translation.x, self.duration, self.pitch + self.y)

    def __sub__(self, other_line_segment):
        """
        Built-in subtract function to support computing a Translation which can translate one LineSegment onto another.
        Input is :type: LineSegment
        Output is :type: Translation, such that self + Translation = LineSegment
        """
        return Translation(self, other_line_segment)

    def __cmp__(self, other_line_segment):
        if self.onset < other_line_segment.onset:
            return -1
        if self.onset == other_line_segment.onset:
            return 0
        if self.onset > other_line_segment.onset:
            return 1

    def __str__(self):
        return "onset {0}, duration {1}, pitch {2}".format(self.onset, self.duration, self.pitch)
    def __repr__(self):
        return "LineSegment(onset={0}, offset={1}, duration={2}, pitch={3})".format(self.onset, self.offset, self.duration, self.pitch)



