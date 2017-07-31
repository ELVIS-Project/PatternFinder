import music21
import logging.config
import os
import yaml

MUSIC21_OUTPUT_PATH = 'patternfinder/music_files/music21_temp_output/'
LOGGING_PATH = 'patternfinder/geometric_helsinki/logging.yaml'

## Music21 User Settings
us = music21.environment.UserSettings()
us['directoryScratch'] = MUSIC21_OUTPUT_PATH
us['graphicsPath'] = '/usr/bin/evince'
us['musicxmlPath'] = '/home/dgarfinkle/MuseScore-2.1-x86_64.AppImage'


## LOGGING
# Add a NullHandler so that logging exceptions are silenced in this library
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Load logging config file
if os.path.exists(LOGGING_PATH):
    with open(LOGGING_PATH, 'rt') as f:
        config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)
else:
    logging.basicConfig(level=logging.INFO)
    logging.warning("%s not found. Using logging.basicConfig at level INFO", LOGGING_PATH)

__all__ = [
        'geometric_helsinki',
        'fanimae'
        ]
