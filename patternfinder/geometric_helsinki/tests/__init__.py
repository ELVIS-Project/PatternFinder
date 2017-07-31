import unittest

from test_lemstrom_example import lemstrom_example_suite
from test_finder import finder_suite

geometric_helsinki_suite = unittest.TestSuite([
    lemstrom_example_suite,
    finder_suite])

