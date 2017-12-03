import unittest
import testtools
import path

from patternfinder.geometric_helsinki import *

from test_exact_matches import exact_matches_suite
from geometric_helsinki import geometric_helsinki_suite

testrunner = unittest.TextTestRunner(verbosity=2)

suites = [
        (2, geometric_helsinki_suite),
        (2, exact_matches_suite)
    ]

def run_all():
    for test in suites:
        result = unittest.TextTestRunner(verbosity=test[0]).run(test[1])


__all__ = [
        'run_all',
        'testrunner',
        'geometric_helsinki_suite',
        'exact_matches_suite'
        ]
