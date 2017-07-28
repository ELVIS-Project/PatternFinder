from finder import Finder
from algorithms import P1, P2, P3, S1, S2, W1, W2
import music21
import logging
import os
import yaml

## LOGGING
# Add a NullHandler so that logging exceptions are silenced in this library
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Music21 User Settings
us = music21.environment.UserSettings()
us['directoryScratch'] = 'music_files/music21_temp_output'

## SETTINGS
SETTINGS_PATH = 'geometric_helsinki/settings.yaml'
# Load default settings
if os.path.exists(SETTINGS_PATH):
    with open(SETTINGS_PATH, 'rt') as f:
        DEFAULT_SETTINGS = yaml.safe_load(f.read())
else:
    logger.warning("'settings.yaml' file not found; we will use the hard-coded"
            + "dictionary stored in " + __name__ + " to determine the default settings")
    DEFAULT_SETTINGS = {
            'algorithm' : 'P1',
            'pattern_window' : 1,
            'source_window' : 5,
            'scale' : pure,
            'threshold' : all,
            'mismatches' : 0,
            'interval_func' : semitones,
            'colour' : red,
            'modify_source' : False,
            'show_pattern' : False,
            'excerpt' : True,
            'auto_select' : True,
            'pattern' : None,
            'source' : None}

# @TODO SETUP.PY
# once we figure out the workflow, we can settle on a package structure and make our setup.py

# @TODO JUPYTER !!!
# also can't do till we settle on the workflow

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