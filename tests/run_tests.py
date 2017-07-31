from unittest import TextTestRunner
#from tests import test_P1, test_P2, test_lemstrom_example, test_exact_matches, test_pange_lingua
from tests import test_lemstrom_example

tests = [
        (2, test_lemstrom_example.LEMSTROM_EXAMPLE_SUITE)
        #(2, test_exact_matches.EXACT_MATCHES_SUITE),
        #(1, test_pange_lingua.PANGE_LINGUA_SUITE),
        #(1, test_P1.P1_SUITE),
        #(1, test_P2.P2_SUITE)
    ]

for test in tests:
    result = TextTestRunner(verbosity=test[0]).run(test[1])

