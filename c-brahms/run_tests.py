from unittest import TextTestRunner
from tests import test_P1, test_P2, test_lemstrom_example

tests = [
        test_P1.P1_SUITE,
        test_P2.P2_SUITE,
        test_lemstrom_example.LEMSTROM_EXAMPLE_SUITE
]

if __name__ == '__main__':
    for test in tests:
        result = TextTestRunner(verbosity=2).run(test)
