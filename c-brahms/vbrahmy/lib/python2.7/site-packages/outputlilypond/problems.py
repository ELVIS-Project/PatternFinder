#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Filename: problems.py
# Purpose: Exceptions and Errors for OutputLilyPond
#
# Copyright (C) 2012, 2013 Christopher Antila
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
Error and warning classes for the outputlilypond module.
"""


class UnidentifiedObjectError(Exception):
    """
    When a music21 object can't be identified.
    """
    pass


class ImpossibleToProcessError(Exception):
    """
    When something is identified, but has an invalid type or property, and cannot be processed.
    """
    pass
