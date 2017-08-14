import unittest
import path
from patternfinder.geometric_helsinki.tests import geometric_helsinki_suite

tests = [
        (2, geometric_helsinki_suite)
    ]

for test in tests:
    result = unittest.TextTestRunner(verbosity=test[0]).run(test[1])

