import unittest
from pprint import pformat

class CustomAssertions(object):
    def assert_equal_occurrences(self, occurrences, expected):
        if len(occurrences) != len(expected):
            raise AssertionError("# of occurrences and # of expected occurrences not the same"
                   + "\n#" + str(len(expected)) + " expected:\n" + pformat(expected)
                   + "\n#" + str(len(occurrences)) + " found:\n" + pformat(occurrences))
        for occurrence, exp in zip(occurrences, expected):
            if occurrence != exp:
                raise AssertionError("Mismatched occurrences"
                        + "\nFOUND:\n" + pformat(occurrence)
                        + "\nEXPECTED\n" + pformat(exp))
