import unittest

import tests.geometric_helsinki

from patternfinder.geometric_helsinki import *

testrunner = unittest.TextTestRunner(verbosity=2)

suites = [
        (2, tests.geometric_helsinki.suite),
    ]

def run_all():
    for test in suites:
        result = unittest.TextTestRunner(verbosity=test[0]).run(test[1])


__all__ = [
        'run_all',
        'testrunner',
        'suites',
        'geometric_helsinki'
        ]
