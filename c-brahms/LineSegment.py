from collections import namedtuple
from copy import deepcopy # For use in LineSegmentSet so as not to modify the original segments when attaching indices
import pdb
import itertools


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

    def __eq__(self, other_vector):
        if self.vector() == other_vector.vector():
            return True
        else:
            return False

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
        self.set_index = None
        self.note = None
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
        Expects a scalar value.  """
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
        return "onset {0}, duration {1}, pitch {2}, set index {3}".format(self.onset, self.duration, self.pitch, self.set_index)
    def __repr__(self):
        msg = "LineSegment(onset={0}, pitch={1}, duration={2})"
        # Include set indices in the repr
        if self.set_index == None:
            msg += "no set"
        else:
            msg = msg + "set index: " + self.set_index
        return msg.format(self.onset, self.pitch, self.duration)

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

class Vector(TwoDVector):
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.v = TwoDVector(end.x - start.x, end.y - start.y)

class LineSegmentSet(list):

    def __init__(self, segments):
        #copy_of_segments = deepcopy(segments)
        #self.extend(copy_of_segments)
        self.extend(segments)

    def set_indices_of_segments(self):
        for i in range(len(self)):
            seg.set_index = i

#   def sort(self, key=None, reverse=None):
        """
        Sorts the list of segments and then reassigns indices to its constituents.
        """
#        super(LineSegmentSet, self).sort(key, reverse)
#        self.set_indices_of_segments()

    def mergeOverlappingSegments(self):
        """
        Merges all overlapping Segments in the Set
        Not strictly pythonic... Could improve by:
            1) sorting the list by pitch and then onset
            2) zip it with itself offset by 1, map .doesOverlapWith, use groupby() and fold .mergeWith on the partitions
        """
        m = len(self)
        for i in range(m):
            j = i + 1
            while j < m:
                if self[i].doesOverlapWith(self[j]):
                    self[i] = self[i].mergeWith(self.pop(j))
                    m -= 1
                j += 1

    def initialize_Ktables(self, S, source_window = 0, pattern_window = 1, start = 0):
        """

        By default, let pattern_window correspond to algorithm S1
        """
        # S souce LineSegmentSet, P pattern LineSegmentSet, w window
        # each table K[i] stores all intra-database vectors (g) which match (g.y = f.y) any intra-pattern vectors (f) starting at p_i (i.e., p_i' - p_i for some i' > i) 
        # so we can loop through all intra_pattern vectors and then find all database vectors which might match each one
        # then use groupby() and dict.fromkeys to make a dictionary of possibly intra-database vectors, hashed to their corresponding g.y's, so it's easily searchable. for each f, go to the f.y bucket in the dict, and loop through the g's that could match it.

        # TODO the last ktable shouldn't have entries? we can't have c == i??

        # Compute all (n choose 2) intra-database vectors, then group them into dictionary buckets based on their g.y values
        S.compute_intra_vectors(window = source_window, start = start)
        self.compute_intra_vectors(window = pattern_window)

        # TODO remove all of these [0]get items by implementing a Translation class which holds line segments which in turn hold set indices
        keyfunc = lambda x: x[0].y
        S.ivs_indices.sort(key=keyfunc)
        intra_database_vectors = {key : list(g) for key, g in itertools.groupby(S.ivs_indices, keyfunc)}

        self.K = []
        for i in range(len(self)):
            self.K.append([])
            for j in range(i+1, min(i+1+pattern_window, len(self))): # j is denoted i' in the paper
#            for j in [min(i+1, len(self)-1)]: # for S1 just consider p_{i+1} - p_{i}
                f = self[j] - self[i]
                # If there are no corresponding intra-database vectors, skip this iteration
# TODO use groupby() and self.ivs so initialize_Ktables becomes algorithm-independent
#        self.K = [[] for elt in self]
#        for i in range(len(self)):
#            f = self[i]
                if not intra_database_vectors.has_key(f.y):
                    continue
                # Otherwise, add them to the table
                for g in intra_database_vectors[f.y]: #TODO raise exception if f.y != g.y?
                    ### TIME SCALING
                    # "if both are zero, set s = 1"
                    if f.x == 0 and g[0].x == 0:
                        scale = 1
                    # "if only one of them equals 0, or both are equal to infinity, delete the row"
                    elif (f.x == float("inf") and g[0].x == float("inf")) or f.x == 0 or g[0].x == 0:
                        continue
                    else:
                        scale = float(g[0].x) / f.x # TODO use fractions

                    # Initialize the hth row of the ith K table
                    #TODO make these vector objects, make TwoDVectors Point objects
                    self.K[i].append({
                        'a' : g[1], #store index of S[i]
                        'b' : g[2], #store index of S[j]
                        'y' : None,
                        'c' : j, #index of P[j]
                        's' : scale,
                        'w' : 1,
                        'z' : 0
                    })
            # Append the last row, denoted \sum{p_i} : the number of rows generated for table K[i]
            self.K[i].append({
                'a' : float("inf"),
                'b' : float("inf"),
                'c' : i + 1,
                's' : 0,
                'w' : 0,
                # y, z are not initialize in the pseudocode but an KeyError is thrown in S2 without them
                'y' : None,
                'z' : 0
            })
            # Sort the K[i]th table in lexicographic order (id of point in source associated with p_i, scaling factor)
            self.K[i].sort(key = lambda x : (x['a'], x['s']))


    #TODO put this in the __init__ method? or an update method? etc.
    # by default, window = len(self) so that if no window is set, compute all vectors
    # use a sorted "self" since this should only take into account positive intra vectors
    def compute_intra_vectors(self, window = 0, start = 0):
        """
        Given a LineSegmentSet, computes all (n choose 2) positive inner-translational vectors
        Can accept a window to ignore vectors which point more than 'w' segments ahead in the list.
        Also can indicate a 'start' point, to ignore any intra-vectors before a certain index.
        Initializes the list of translations in self.ivs
        """
        # TODO make it so window = 0 means no window, so you don't need len(patterns) when you call this function
        #TODO get rid of the "start" functionality? it was just to test lemstrom
#        self.sort()
#        self.ivs = [(self[j] - self[i]) for i in range(start, len(self)) for j in range(i + 1, min(i + 1 + window, len(self)))]

        sorted_self = sorted(self)

        # Find all non-duplicate pairs (up to some window) of intra-database vectors and sort them by their x translations.
        # range(i+1, min(i+1 + window, len(self))) -- example: say w=3, len(self) > 23, and i=20. we should get vectors for 20->21, 20->22, 20->23
        # this would evaluate to: for j in range(21, 21 + 3) --> [21, 22, 23]. Remember range(x,y) starts at 0 and ends at y-1 !!!

        self.ivs_indices = sorted([(sorted_self[j] - sorted_self[i], i, j) for i in range(start, len(self)) for j in range(i+1, min(i+1 + window, len(self)))], key = lambda x: x[0].y)
        self.ivs = sorted([sorted_self[j] - sorted_self[i] for i in range(start, len(self)) for j in range(i+1, min(i+1 + window, len(self)))], key = lambda x: x.y)

        # Return hashed buckets where each unique x translation has its own bucket of intra-database vectors and corresponding indices
#        self.ivs = {key : list(g) for key, g in itertools.groupby(intra_database_vectors, keyfunc)}

    def onsets_with_notes(self):
        return zip(self.onsets, self.notes)
    def offsets_with_notes(self):
        return zip(self.offsets, self.notes)
