from unittest import TextTestRunner
from tests import test_midiparser
from tests import test_ngr5
from tests import test_pioi

tests = [test_midiparser.MIDIPARSER_SUITE,
         test_ngr5.NGR5_SUITE,
         test_pioi.PIOI_SUITE]

if __name__ == '__main__':
    for test in tests:
        result = TextTestRunner(verbosity=0, descriptions=False).run(test)
