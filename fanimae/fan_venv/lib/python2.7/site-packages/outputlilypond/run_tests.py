#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Filename: run_tests.py
# Purpose: Run automated tests for the outputlilypond module.
#
# Copyright (C) 2012, 2013, 2014 Christopher Antila
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#--------------------------------------------------------------------------------------------------
"""
Run automated tests for the outputlilypond module.
"""

# Ensure we can import "outputlilypond"
import imp
try:
    imp.find_module(u'outputlilypond')
except ImportError:
    import sys
    sys.path.insert(0, u'..')

import unittest
from outputlilypond.tests import unit_tests, integration_tests, settings

if __name__ == '__main__':
    VERBOSITY = 1

    # Unit Tests
    unittest.TextTestRunner(verbosity=VERBOSITY).run(settings.SETTINGS_SUITE)
    unittest.TextTestRunner(verbosity=VERBOSITY).run(settings.DETECT_LILYPOND_SUITE)
    unittest.TextTestRunner(verbosity=VERBOSITY).run(unit_tests.OCTAVENUM_SUITE)
    unittest.TextTestRunner(verbosity=VERBOSITY).run(unit_tests.PITCH_SUITE)
    unittest.TextTestRunner(verbosity=VERBOSITY).run(unit_tests.DURATION_SUITE)
    unittest.TextTestRunner(verbosity=VERBOSITY).run(unit_tests.NOTE_SUITE)
    unittest.TextTestRunner(verbosity=VERBOSITY).run(unit_tests.BARLINE_SUITE)
    unittest.TextTestRunner(verbosity=VERBOSITY).run(unit_tests.CLEF_SUITE)
    unittest.TextTestRunner(verbosity=VERBOSITY).run(unit_tests.CHORD_SUITE)
    unittest.TextTestRunner(verbosity=VERBOSITY).run(unit_tests.METADATA_SUITE)

    # Integration Tests
    unittest.TextTestRunner(verbosity=VERBOSITY).run(integration_tests.MEASURE_SUITE)
    unittest.TextTestRunner(verbosity=VERBOSITY).run(integration_tests.STREAM_SUITE)
