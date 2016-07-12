#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Filename: __init__.py
# Purpose: Init file for outputlilypond
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
Init file for outputlilypond.
"""

# Ensure we can import "outputlilypond"
import imp
try:
    imp.find_module(u'outputlilypond')
except ImportError:
    import sys
    sys.path.insert(0, u'..')

from outputlilypond.__main__ import run_lilypond, process_score
