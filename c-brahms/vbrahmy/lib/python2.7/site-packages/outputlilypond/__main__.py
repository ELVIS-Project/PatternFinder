#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Filename: __main__.py
# Purpose: Principal file for the outputlilypond module.
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
Output music21 objects into their respective LilyPond representation. This library is intended for
music research software.

Use :mod:`outputlilypond` by calling :func:`process_score` then :func:`run_lilypond`. You may wish
to use your own :class:`settings.LilyPondSettings` object to change the way :mod:`outputlilypond`
behaves.

You may also use our module-level functions (located in the :mod:`outputlilypond.functions` module)
for other tasks, but we do not recommend you use :func:`process_score` along with other
module-level functions.
"""

import os
from subprocess import Popen, PIPE
from multiprocessing import Pool
from music21 import stream, converter
from outputlilypond import functions, settings


def run_lilypond(filename, the_settings=None):
    """
    Run LilyPond on a file.

    :param filename: The full pathname to the file on which to run LilyPond.
    :type filename: string
    :param the_settings: An optional settings object.
    :type the_settings: :class:`settings.LilyPondSettings`
    """
    if the_settings is None:
        the_settings = settings.LilyPondSettings()

    # Make the PDF filename; make sure we don't output to "*.ly.pdf"
    pdf_filename = ''
    if 3 < len(filename) and '.ly' == filename[-3:]:
        pdf_filename = filename[:-3]
    else:
        pdf_filename = filename

    # NB: this method returns something that might be interesting
    # NB2: this try/except block means, practically, that we'll use Popen (which is better) on
    # Linux, but where it fails (OS X), we'll use os.system()
    try:
        cmd = [the_settings.get_property('lilypond_path'), '-dno-point-and-click', '-dsafe=#t', '--pdf', '-o', pdf_filename, filename]
        lily = Popen(cmd, stdout=PIPE, stderr=PIPE)
        lily.communicate(input=None)  # wait for 'lilypond' to exit; returns stdout
    except OSError:
        os.system('%s -dno-point-and-click -dsafe=#t --pdf -o %s %s' %
                  (the_settings.get_property('lilypond_path'), pdf_filename, filename))


def process_score(the_score, the_settings=None):
    """
    Convert an entire :class:`music21.stream.Stream` object, nominally a :class:`Score`, into a
    unicode string for output as a LilyPond source file.

    :param the_score: The :class:`Stream` to output. This method works on any type of
        :class:`Stream`, but uses multiprocessing only for :class:`Score` objects.
    :type the_score: :class:`music21.stream.Stream`
    :param the_settings: An optional settings object that will be passed to all client functions.
        Use this object to modify runtime behaviour.
    :type the_settings: :class:`settings.LilyPondSettings`

    :returns: A string that holds an entire LilyPond source file (as complete as possible for the
        type of :class:`Stream` object provided).
    :rtype: ``unicode``
    """
    the_settings = settings.LilyPondSettings() if the_settings is None else the_settings
    if isinstance(the_score, stream.Score):
        # multiprocessing!
        return LilyMultiprocessor(the_score, the_settings).run()
    else:
        # not sure what to do here... guess we'll default to old style?
        # TODO: this won't work as-is
        return functions.stream_to_lily(the_score, the_settings)


class LilyMultiprocessor(object):
    "Manage multiprocessing for outputlilypond."

    def __init__(self, score, setts):
        """
        Create a new LilyMultiprocessor instance.
        """
        super(LilyMultiprocessor, self).__init__()
        self._score = score
        self._setts = setts
        self._pool = Pool()
        self._finished_parts = []
        self._final_result = None

    def callback(self, result):
        """
        For internal use.

        Called when :func:`functions.stream_to_lily` has finished converting an object to its
        LilyPond representation.The method adds the resulting string to the internal list of
        analyses.
        """
        # we have to put things in their proper indices!
        self._finished_parts[result[0]] = result[1]
        self._setts._parts_in_this_score[result[0]] = result[2]
        if 0 == len(self._score):
            print('outputlilypond: zero-length Score...')  # wish we had a better solution
        if hasattr(self._score[result[0]], u'lily_analysis_voice') and \
        self._score[result[0]].lily_analysis_voice is True:
            self._setts._analysis_notation_parts.append(result[2])

    def run(self):
        """
        Process all the parts! Prepare a score!
        """

        # Things Before Parts:
        # Our mark! // Version // Paper size
        post = [u'%% LilyPond output from music21 via "outputlilypond"\n'
                u'\\version "%s"\n'
                u'\n'
                u'\\paper {\n'
                u'\t#(set-paper-size "%s")\n'
                u'\t#(define left-margin (* 1.5 cm))\n'  # TODO: this should be a setting
                u'}\n\n' % (self._setts.get_property('lilypond_version'),
                            self._setts.get_property('paper_size'))]

        # Parts:
        # Initialize the length of finished "parts" (maybe they're other things, too, like Metadata
        # or whatever... doesn't really matter).
        self._finished_parts = [None for i in xrange(len(self._score))]
        self._setts._parts_in_this_score = [None for i in xrange(len(self._score))]

        # Go through the possible parts and see what we find.
        for i in xrange(len(self._score)):
            if isinstance(self._score[i], stream.Part):
                if hasattr(self._score[i], u'lily_analysis_voice') and \
                self._score[i].lily_analysis_voice is True:
                    self._setts._analysis_notation_parts.append(i)
                self._pool.apply_async(functions.stream_to_lily,
                                       (converter.freezeStr(self._score[i]), self._setts, i),
                                       callback=self.callback)
            else:
                self._finished_parts[i] = functions.stream_to_lily(self._score[i], self._setts)

        # Wait for the multiprocessing to finish
        self._pool.close()
        self._pool.join()
        del self._pool

        # Append the parts to the score we're building. In the future, it'll be important to
        # re-arrange the parts if necessary, or maybe to filter things, so we'll keep everything
        # in this supposedly efficient loop.
        for i in xrange(len(self._finished_parts)):
            if self._finished_parts[i] != u'' and self._finished_parts[i] is not None:
                post.append(self._finished_parts[i] + u'\n')

        # Things After Parts
        # Output the \score{} block
        post.append(u'\\score {\n\t\\new StaffGroup\n\t<<\n')
        for each_part in self._setts._parts_in_this_score:
            if each_part is None:
                continue
            elif each_part in self._setts._analysis_notation_parts:
                post.extend([u'\t\t\\new VisAnnotation = "', each_part, u'" \\' + each_part + u'\n'])
            else:
                post.extend([u'\t\t\\new Staff = "', each_part, u'" \\' + each_part + u'\n'])
        post.append(u'\t>>\n')

        # Output the \layout{} block
        post.append(u'\t\\layout{\n')
        if self._setts.get_property('indent') is not None:
            post.extend([u'\t\tindent = ', self._setts.get_property('indent'), u'\n'])
        post.append("""\t\t% VisAnnotation Context
\t\t\\context
\t\t{
\t\t\t\\type "Engraver_group"
\t\t\t\\name VisAnnotation
\t\t\t\\alias Staff
\t\t\t\\consists "Output_property_engraver"
\t\t\t\\consists "Script_engraver"
\t\t\t\\consists "Text_engraver"
\t\t\t\\consists "Axis_group_engraver"
\t\t\t\\consists "Instrument_name_engraver"
\t\t}
\t\t% End VisAnnotation Context
\t\t
\t\t% Modify "StaffGroup" context to accept VisAnnotation context.
\t\t\\context
\t\t{
\t\t\t\\StaffGroup
\t\t\t\\accepts VisAnnotation
\t\t}
\t}\n}\n
""")

        self._final_result = u''.join(post)

        # Return the "finished score"
        return self._final_result
