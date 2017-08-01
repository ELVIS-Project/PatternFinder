import music21
import logging
import os
import yaml

from algorithms import P1, P2, P3, S1, S2, W1, W2
from finder import Finder

## Load test suites for geometric_helsinki
import unittest
import doctest
import finder

from tests.test_lemstrom_example import lemstrom_example_suite
from tests.test_finder import finder_suite

geometric_helsinki_suite = unittest.TestSuite([
    # Lemstrom queries A-F
    lemstrom_example_suite,
    # Test the Finder object
    finder_suite,
    # Doctests for the Finder object
    doctest.DocTestSuite(finder)])


## Define from geometric_helsinki import *
__all__ = [
        'Finder'
        ]

# @TODO ALGORITHMS Test interval settings, also why is it broken on the fugues?

# @TODO LOGGERS
# Make loggers for each algorithm, store it in the init, so we can choose which ones we get output from?
# do we need to test loggers?

# @TODO MULTIPLE CHAINS
# we should be able to identify when P2, S2, W2 with mismatch > 0 returns all combinations of mismatches
# within a perfect match. I think we can do this by giving each intra vector an occurrence ID which it 







# passes along to each subsequent chain it extends

# From todo.txt
#Remaining:
#8) test cases with partly-overlapping voices. we should get different behaviour for each algorithms, and we should test it. should P3 get more than one shift? when does P1 get more than one shift?

#6)python find_matches.py P1 music_files/schubert_soggettos/casulana1.xml music_files/schubert_soggettos/Casulan2-4-2.xml  will find a match at offset 18, transposition 17, with intersection length of 8. meaning hte first note of the query (c in the bass) should match to a note 17 semitones above (bottom space f in treble) - but there is no F in measure 3 of the source!! UGH
