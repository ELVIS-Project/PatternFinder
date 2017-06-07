from finder import Finder
from algorithms import P1, P2, P3, S1, S2, W1, W2

# @TODO SETUP.PY
# once we figure out the workflow, we can settle on a package structure and make our setup.py

# @TODO JUPYTER !!!
# also can't do till we settle on the workflow

# @TODO ALGORITHMS Test interval settings, also why is it broken on the fugues?

# @TODO LOGGERS
# Make loggers for each algorithm, store it in the init, so we can choose which ones we get output from?
# do we need to test loggers?

# From todo.txt
#Remaining:
#8) test cases with partly-overlapping voices. we should get different behaviour for each algorithms, and we should test it. should P3 get more than one shift? when does P1 get more than one shift?

#6)python find_matches.py P1 music_files/schubert_soggettos/casulana1.xml music_files/schubert_soggettos/Casulan2-4-2.xml  will find a match at offset 18, transposition 17, with intersection length of 8. meaning hte first note of the query (c in the bass) should match to a note 17 semitones above (bottom space f in treble) - but there is no F in measure 3 of the source!! UGH
