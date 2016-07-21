from unittest import TextTestRunner
from tests import cbrahmsGeoTest

tests = [cbrahmsGeoTest.CBRAHMSTestP1_SUITE]

if __name__ == '__main__':
    for test in tests:
        result = TextTestRunner(verbosity=2).run(test)
