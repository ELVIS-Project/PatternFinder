import unittest
import doctest

from patternfinder.geometric_helsinki import finder

from tests.geometric_helsinki.test_lemstrom_example import lemstrom_example_suite
from tests.geometric_helsinki.test_finder import finder_suite
from tests.geometric_helsinki.test_algorithms import geometric_helsinki_overlapping_voices_suite
from tests.geometric_helsinki.test_exact_matches import exact_matches_suite

finder_doctest_suite = doctest.DocTestSuite(finder)

## GEOMETRIC_HELSINKI TEST SUITE DEFINITION
suite = unittest.TestSuite([
    # Lemstrom queries A-F
    lemstrom_example_suite,
    # Test the Finder object
    finder_suite,
    # Doctests for the Finder object
    finder_doctest_suite,
    # Algorithm tests
    geometric_helsinki_overlapping_voices_suite,
    # Exact Matches tests
    exact_matches_suite])
