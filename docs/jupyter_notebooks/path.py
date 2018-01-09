import sys
import os
import music21
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '/home/dgarfinkle/PatternFinder')))
os.chdir('/home/dgarfinkle/PatternFinder/')

os.environ['QT_QPA_PLATFORM'] = 'offscreen'

us = music21.environment.UserSettings()
us['musicxmlPath'] = '/usr/bin/musescore'
us['musescoreDirectPNGPath'] = '/usr/bin/musescore'
us['ipythonShowFormat'] = 'ipython.musicxml.png'
us['showFormat'] = 'musicxml'
us['pdfPath'] = '/usr/bin/evince'
us['lilypondPath'] = '/usr/bin/lilypond'

