#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Filename: functions.py
# Purpose: Converter functions used by outputlilypond.
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
Converter functions used by outputlilypond.
"""


import random
from itertools import repeat
from music21 import clef, duration, chord, note, key, meter, layout, expressions, humdrum, bar, \
    stream, instrument, tempo, converter, metadata, text
from outputlilypond import problems, settings


"""
Clef-to-string equivalencies used by :func:`clef_to_lily`.
"""
CLEF_DICT = {clef.Treble8vbClef: u"\\clef \"treble_8\"",
             clef.Treble8vaClef: u"\\clef \"treble^8\"",
             clef.Bass8vbClef: u"\\clef \"bass_8\"",
             clef.Bass8vaClef: u"\\clef \"bass^8\"",
             clef.TrebleClef: u"\\clef treble",
             clef.BassClef: u"\\clef bass",
             clef.TenorClef: u"\\clef tenor",
             clef.AltoClef: u"\\clef alto",
             clef.FBaritoneClef: u"\\clef varbaritone",
             clef.CBaritoneClef: u"\\clef baritone",
             clef.FrenchViolinClef: u"\\clef french",
             clef.MezzoSopranoClef: u"\\clef mezzosoprano",
             clef.PercussionClef: u"\\clef percussion",
             clef.SopranoClef: u"\\clef soprano",
             clef.SubBassClef: u"\\clef subbass"}

"""
Barline-to-string equivalencies used by :func:`barline_to_lily`.
"""
BARLINE_DICT = {'regular': u"|", 'dotted': u":", 'dashed': u"dashed", 'heavy': u"|.|",
                'double': u"||", 'final': u"|.", 'heavy-light': u".|", 'heavy-heavy': u".|.",
                'tick': u"'", 'short': u"'", 'none': u""}

"""
Quarter-length-to-string equivalencies used by :func:`duration_to_lily`.
"""
DURATION_DICT = {16.0: u'\\longa', 8.0: u'\\breve', 4.0: u'1', 2.0: u'2', 1.0: u'4', 0.5: u'8',
                 0.25: u'16', 0.125: u'32', 0.0625: u'64', 0.03125: u'128'}


"""
Octave-number-to-string equivalencies used by :func:`octave_num_to_lily`.
"""
OCTAVE_DICT = {0: u",,,", 1: u",,", 2: u",", 3: u"", 4: u"'", 5: u"''", 6: u"'''", 7: u"''''",
               8: u"'''''", 9: u"''''''", 10: u"'''''''", 11: u"''''''''", 12: u"'''''''''"}


def string_of_n_letters(n):
    """
    Generate a string of ``n`` pseudo-random letters.

    This function is currently used to help create unique part names in scores.

    :param n: How long the output string should be.
    :type n: integer

    :returns: A string of ``n`` pseudo-random lowercase letters.
    :rtype: unicode string
    """
    if 0 == n:
        return u''
    else:
        return random.choice(u'qwertyuiopasdfghjklzxcvbnm') + string_of_n_letters(n - 1)


def clef_to_lily(the_clef, append=u'\n', invisible=False):
    """
    Convert a :class:`music21.clef.Clef` object into the LilyPond string.

    :param the_clef: The :class:`Clef` to convert. It must be recognized in :const:`CLEF_DICT`.
    :type the_clef: :class:`~music21.clef.Clef` subclass.
    :param append: An optional string to append to the clef string; the default is ``u'\n'``,
        representing a newline character.
    :type append: string
    :param invisible: Whether to override the ``#'transparent`` property to ``##t``; the default is
        ``False``.
    :type invisible: boolean

    :returns: The LilyPond-format notation for this clef.
    :rtype: unicode string

    :raises: :exc:`UnidentifiedObjectError` if the :class:`Clef` is not of a known type.
    """
    post = u"\\once \\override Staff.Clef #'transparent = ##t" + append if invisible else u''
    try:
        return post + CLEF_DICT[type(the_clef)] + append
    except KeyError:
        raise problems.UnidentifiedObjectError('Clef type not recognized: ' + unicode(the_clef))


def barline_to_lily(barline):
    """
    Convert a :class:`Barline` object into the LilyPond string.

    Parameters
    ----------

    :param barline: The barline to convert. It must be recognized in :const:`BARLINE_DICT`.
    :type barline: :class:`music21.bar.Barline`

    :returns: The LilyPond-format notation for this barline.
    :rtype: unicode string

    :raises: :exc:`UnidentifiedObjectError` if the :class:`Barline`'s ``style`` attribute is not of
        a known type.
    """
    try:
        return u'\\bar "' + BARLINE_DICT[barline.style] + u'"'
    except KeyError:
        err = 'Barline type not recognized (' + barline.style + ')'
        raise problems.UnidentifiedObjectError(''.join(err))


def duration_to_lily(dur, known_tuplet=False):
    """
    Convert a :class:`Duration` into the LilyPond string.

    :param dur: The duration to convert.
    :type dur: :class:`music21.duration.Duration`
    :param known_tuplet: Whether we already know this duration is part of a tuplet. (Default is
        ``False``).
    :type known_tuplet: boolean

    :returns: The LilyPond-format notation for this duration.
    :rtype: unicode string

    :raises: :exc:`ImpossibleToProcessError` if ``dur`` is part of a tuplet but ``known_tuplet`` is
        ``False``, since this requires a ``\\tuplet`` command in LilyPond.
    :raises: :exc:`ImpossibleToProcessError` if ``dur.quarterLength == 0.0`` is ``True``, since
        LilyPond has no zero-duration duration.
    """

    # Every Duration should actually have some duration.
    if 0.0 == dur.quarterLength:
        msg = u'_duration_to_lily(): Cannot process quarterLength of 0.0'
        raise problems.ImpossibleToProcessError(msg)

    # First of all, we can't deal with tuplets or multiple-component durations
    # in this method. We need process_measure() to help.
    if dur.tuplets is not ():
        # We know either there are multiple components or we have part of a
        # tuplet, we we need to find out which.
        if len(dur.components) > 1:
            # We have multiple components
            raise problems.ImpossibleToProcessError('Cannot process durations with ' +
                'multiple components (received ' + unicode(dur.components) +
                ' for quarterLength of ' + unicode(dur.quarterLength) + ')')
        elif known_tuplet:
            # We have part of a tuple. This isn't necessarily a problem; we'll
            # assume we are given this by process_measure() and that it knows
            # what's going on. But, in tuplets, the quarterLength doesn't match
            # the type of written note, so we'll make a new Duration with an
            # adjusted quarterLength
            dur = duration.Duration(dur.type)
        else:
            msg = 'duration_to_lily(): Cannot process tuplet components'
            raise problems.ImpossibleToProcessError(msg)

    dur_ql = dur.quarterLength
    # If there are no dots, the value should be in the dictionary, and we can simply return it.
    if dur_ql in DURATION_DICT:
        return DURATION_DICT[dur_ql]
    else:
        # We have to figure out the largest value that will fit, then append some dots.
        post = None
        for durat in sorted(DURATION_DICT.keys(), reverse=True):  # we need largest-to-smallest qLs
            if (dur_ql - durat) > 0.0:
                post = DURATION_DICT[durat]
                break
        # For every dot in this Duration, append a '.' to "post"
        for _ in repeat(None, dur.dots):
            post += u'.'
        return post


def octave_num_to_lily(num):
    """
    Convert an octave number into the LilyPond string.

    :param num: The octave number to convert. As expected, ``4`` is the "middle C" register.
    :type num: int

    :returns: The string to append to a pitch to put it in the specified octave.
    :rtype: unicode string

    ** Examples **

    >>> octave_num_to_lily(1)
    u",,"
    >>> octave_num_to_lily(6)
    u"'''"
    """
    try:
        return OCTAVE_DICT[num]
    except KeyError:
        raise problems.UnidentifiedObjectError('Octave out of range: ' + unicode(num))


def pitch_to_lily(the_pitch, include_octave=True):
    """
    Convert a :class:`Pitch` into the LilyPond string.

    :param the_pitch: The :class:`Pitch` to convert.
    :type the_pitch: :class:`music21.pitch.Pitch`
    :param include_octave: Whether to include the octave marks in the output. Default is ``True``.
    :type include_octave: boolean

    :returns: The LilyPond-format notation for this pitch.
    :rtype: unicode string
    """
    pclass = the_pitch.name.lower()
    post = [pclass[0]]

    for accidental in pclass[1:]:
        if '-' == accidental:
            post.append(u'es')
        elif '#' == accidental:
            post.append(u'is')

    if include_octave is True:
        if the_pitch.octave is None:
            post.append(octave_num_to_lily(the_pitch.implicitOctave))
        else:
            post.append(octave_num_to_lily(the_pitch.octave))

    return ''.join(post)


def note_to_lily(the_note, known_tuplet=False):
    """
    Convert a :class:`Chord`, :class:`Note`, or :class:`Rest` into the LilyPond string.

    :param the_note: The note or rest to convert.
    :type known_note: :class:`music21.chord.Chord`, :class:`music21.note.Note`, or
        :class:`music21.note.Rest`
    :param known_tuplet: Whether we already know this note is part of a tuplet. (Default is
        ``False``).
    :type known_tuplet: boolean

    :returns: The LilyPond-format notation for this note.
    :rtype: unicode string

    ** Special Attributes **

    Set these two attributes on the :class:`Chord`, :class:`Note`, or :class:`Rest` itself:

    * ``lily_invisible`` (boolean): Print the object as an invisible spacer (with ``u's'`` as the
        pitch).
    * ``lily_markup`` (string): This string will be appended after (to the right of) the rest of
        the note/rest/spacer's code. The intended purpose is to use this with a ``\\markup``
        command, but you may also use it, for example, to add beam-start and beam-end characters.
    """
    post = []

    # Find the letter: either 's', '<whatever>' for a chord, 'r' for a rest, etc.
    if hasattr(the_note, 'lily_invisible') and the_note.lily_invisible is True:
        post.append(u's')
    elif isinstance(the_note, chord.Chord):
        # Add the pitch letters and register numbers
        the_pitches = [u'<']
        for each_pitch in the_note.pitches:
            the_pitches.extend([pitch_to_lily(each_pitch), u' '])
        the_pitches = the_pitches[:-1]  # remove trailing space
        the_pitches.append(u'>')  # add chord-end symbol
        post.append(u''.join(the_pitches))
    elif the_note.isRest:
        post.append(u'r')
    else:
        post.append(pitch_to_lily(the_note.pitch))

    # Find the duration(s)
    if len(the_note.duration.components) > 1:
        post.extend([duration_to_lily(the_note.duration.components[0], known_tuplet), u'~ '])
        # We have a multiple-part duration
        for component in the_note.duration.components[1:]:
            post.extend([post[0], duration_to_lily(component, known_tuplet), u'~ '])
        post = post[:-1]  # remove the final tilde symbol
    else:
        # Just a straightforward duration
        post.append(duration_to_lily(the_note.duration, known_tuplet))

    # Add a tie if necessary
    if the_note.tie is not None:
        if u'start' == the_note.tie.type:
            post.append(u'~')

    if hasattr(the_note, 'lily_markup'):
        post.append(unicode(the_note.lily_markup))

    return u''.join(post)


def measure_to_lily(meas, incomplete=False):
    """
    Convert a :class:`Measure` into the LilyPond string.

    :param meas: The :class:`Measure` to convert.
    :type mease: :class:`music21.stream.Measure`
    :param incomplete: Whether to check whether the :class:`Measure` is (durationally) incomplete.
        The default is ``False``.
    :type incomplete: boolean

    :returns: The LilyPond-format notation for this measure.
    :rtype: unicode string

    ** Special Attributes **

    Attach this attribute to the :class:`Measure` itself:

    * ``lily_invisible`` (boolean): Make the :class:`Measure` and its contents invisible.
    """

    post = [u"\t"]
    barcheck_included = False

    # Hold whether this Measure is supposed to be "invisible"
    invisible = False
    if hasattr(meas, 'lily_invisible'):
        invisible = meas.lily_invisible

    # Add the first requirement of invisibility
    if invisible:
        post.append(u'\\stopStaff\n\t')

    # first check if it's a partial (pick-up) measure
    if incomplete:
        bar_dur = meas.barDuration.quarterLength
        my_dur = meas.duration.quarterLength
        if round(my_dur, 2) < bar_dur:
            if meas.duration.components is not None:
                rounded = duration.Duration(round(my_dur, 2))
                post.extend([u"\\partial ", duration_to_lily(rounded), u"\n\t"])
            else:
                post.extend([u"\\partial ", duration_to_lily(meas.duration), u"\n\t"])

    # Make meas an iterable, so we can pull in multiple elements when we need to deal
    # with tuplets.
    bar_iter = iter(meas)
    # This holds \markup{} blocks that happened before a Note/Rest, and should be appended
    # to the next Note/Rest that happens.
    attach_this_markup = u''
    # And fill in all the stuff
    for obj in bar_iter:
        # Note or Rest
        if isinstance(obj, note.Note) or isinstance(obj, note.Rest):
            # TODO: is there a situation where I'll ever need to deal with
            # multiple-component durations for a single Note/Rest?
            # ANSWER: yes, sometimes

            # Is it a full-measure rest?
            if isinstance(obj, note.Rest) and \
            bar_iter.srcStream.barDuration.quarterLength == obj.quarterLength:
                if invisible:
                    post.extend(['s', duration_to_lily(obj.duration), u' '])
                else:
                    post.extend([u'R', duration_to_lily(obj.duration), u' '])
            # Is it the start of a tuplet?
            elif obj.duration.tuplets is not None and len(obj.duration.tuplets) > 0:
                number_of_tuplet_components = obj.duration.tuplets[0].numberNotesActual
                in_the_space_of = obj.duration.tuplets[0].numberNotesNormal
                post.extend([u'\\times ', unicode(in_the_space_of), u'/',
                    unicode(number_of_tuplet_components), u' { ',
                    note_to_lily(obj, True), u" "])
                # For every tuplet component...
                for _ in repeat(None, number_of_tuplet_components - 1):
                    post.extend([note_to_lily(next(bar_iter), True), u' '])
                post.append(u'} ')
            # It's just a regular note or rest
            else:
                post.extend([note_to_lily(obj), u' '])

            # Is there a \markup{} block to append?
            if attach_this_markup != '':
                post.append(attach_this_markup)
                attach_this_markup = ''
        # Chord
        elif isinstance(obj, chord.Chord):
            post.extend([note_to_lily(obj), u' '])
        # Clef
        elif isinstance(obj, clef.Clef):
            post.extend([clef_to_lily(obj, append=u'\n\t', invisible=invisible)])
        # Time Signature
        elif isinstance(obj, meter.TimeSignature):
            if invisible:
                post.append(u"\\once \\override Staff.TimeSignature #'transparent = ##t\n\t")
            post.extend([u"\\time ",
                unicode(obj.beatCount), "/",
                unicode(obj.denominator), u"\n\t"])
        # Key Signature
        elif isinstance(obj, key.KeySignature):
            pitch_and_mode = obj.pitchAndMode
            if invisible:
                post.append(u"\\once \\override Staff.KeySignature #'transparent = ##t\n\t")
            if 2 == len(pitch_and_mode) and pitch_and_mode[1] is not None:
                post.extend([u"\\key ",
                             pitch_to_lily(pitch_and_mode[0], include_octave=False),
                             u" \\" + pitch_and_mode[1] + "\n\t"])
            else:
                # We'll have to assume it's \major, because music21 does that.
                post.extend([u"\\key ",
                             pitch_to_lily(pitch_and_mode[0], include_octave=False),
                             u" \\major\n\t"])
        # Barline
        elif isinstance(obj, bar.Barline):
            # We don't need to write down a regular barline, but either way, we definitely
            # should include a bar-check symbol
            barcheck_included = True
            if 'regular' != obj.style:
                post.extend([u'|\n', u'\t', barline_to_lily(obj), u'\n'])
            else:
                post.append(u'|\n')
        # PageLayout and SystemLayout
        elif isinstance(obj, layout.SystemLayout) or isinstance(obj, layout.PageLayout):
            # I don't know what to do with these undocumented features.
            # NB: They now have documentation, so I could check up on this...
            pass
        # **kern importer garbage... well, it's only garbage to us
        elif isinstance(obj, humdrum.spineParser.MiscTandem):
            # http://mit.edu/music21/doc/html/moduleHumdrumSpineParser.html
            # Is there really nothing we can use this for? Seems like these
            # exist only to help music21 developers.
            pass
        elif isinstance(obj, humdrum.spineParser.SpineComment):
            # http://mit.edu/music21/doc/html/moduleHumdrumSpineParser.html
            # These contain at least part names, and maybe also other interesting metadata(?)
            pass
        # Written expression marks (like "con fuoco" or something)
        elif isinstance(obj, expressions.TextExpression):
            the_marker = None  # store the local thing
            if obj.positionVertical > 0:  # above staff
                the_marker = [u"^\\markup{ "]
            elif obj.positionVertical < 0:  # below staff
                the_marker = [u"_\\markup{ "]
            else:  # LilyPond can decide above or below
                the_marker = [u"-\\markup{ "]
            if obj.enclosure is not None:  # put a shape around the text?
                pass  # TODO
            the_marker.extend([u'"', obj.content, u'" }'])
            if obj.enclosure is not None:  # must close the enclosure, if necessary
                the_marker.append(u'}')
            the_marker.append(u' ')

            # Find out whether there's a previous Note or Rest to attach to
            previous_element = meas.getElementBeforeOffset(obj.offset)
            if not isinstance(previous_element, note.Note) and \
            not isinstance(previous_element, note.Rest):
                # this variable holds text to append to the next Note/Rest
                attach_this_markup = u''.join([attach_this_markup, the_marker])
            else:  # There was a previous Note/Rest, so we're good
                post.append(u''.join(the_marker))
            del the_marker
        elif isinstance(obj, layout.StaffLayout):  # as in the Lassus duos
            # TODO: something more useful
            pass
        # We don't know what it is, and should probably figure out!
        else:
            pass
            #msg = u'Unknown object in m.%s of type %s.' % (meas.number, type(obj))
            #print(msg)  # DEBUG
            #raise UnidentifiedObjectError(msg)

    # Append a bar-check symbol, if relevant
    if len(post) > 1 and not barcheck_included:
        post.append(u"|\n")

    # Append a note if we couldn't include a \markup{} block
    if attach_this_markup != '':
        post.extend(u'% Could not include this markup: ', attach_this_markup)

    # The final requirement of invisibility
    if invisible:
        post.append(u'\t\\startStaff\n')

    return u''.join(post)


def analysis_part_to_lily(part):
    """
    Convert a :class:`Part` with analytic markings into the LilyPond string.

    This means the :class:`Part`'s ``lily_analysis_voice`` attribute is ``True``. The resulting
    part has no staff lines, is printed in its score order, and has all ``lily_markup`` attributes
    attached to "spacer" notes (i.e., with the letter name ``s``).

    :param part: The :class:`Part` to convert; it should have only :class:`~music21.note.Note`
        objects.
    :type part: :class:`music21.stream.Part`

    :returns: The LilyPond-format notation for this analysis part.
    :rtype: unicode string
    """
    post = []
    for obj in part:
        obj.lily_invisible = True
        post.extend([u'\t', note_to_lily(obj), u'\n'])
    return u''.join(post)


def metadata_to_lily(metad, setts=None):
    """
    Convert a :class:`Metadata` object into the LilyPond string.

    :param metad: The :class:`Metadata` object to convert.
    :type metad: :class:`music21.metadata.Metadata`
    :param setts: An optional settings object.
    :type setts: :class:`~settings.LilyPondSettings`

    :returns: The LilyPond-format notation for this metadata object.
    :rtype: unicode string
    """

    if setts is None:
        setts = settings.LilyPondSettings()

    post = [u"\\header {\n"]

    if metad.composer is not None:
        post.extend([u'\tcomposer = \\markup{ "', metad.composer, u'" }\n'])
    if u'None' != unicode(metad.date):
        post.extend([u'\tdate = "', unicode(metad.date), u'"\n'])
    if metad.movementName is not None:
        if None != metad.movementNumber:
            post.extend([u'\tsubtitle = \\markup{ "',
                         unicode(metad.movementNumber), u': ',
                         metad.movementName, u'" }\n'])
        else:
            post.extend([u'\tsubtitle = \\markup{ "',
                         metad.movementName, u'" }\n'])
    if metad.opusNumber is not None:
        post.extend([u'\topus = "', unicode(metad.opusNumber), u'"\n'])
    if metad.title is not None:
        if metad.alternativeTitle is not None:
            post.extend([u'\ttitle = \\markup{ \"', metad.title,
                         u'(\\"' + metad.alternativeTitle + u'\\")', u'" }\n'])
        else:
            post.extend([u'\ttitle = \\markup{ \"', metad.title, u'" }\n'])
    # Extra Formatting Options
    if setts.get_property('tagline') is None:
        post.append(u'\ttagline = ""\n')
    else:
        post.extend([u'\ttagline = "', setts.get_property('tagline'), '"\n'])
    # close the \header{} block, join, and return!
    post.append(u"}\n")
    return u''.join(post)


def part_to_lily(part, setts):
    """
    Convert a :class:`Part` object into the LilyPond string.

    :param part: The :class:`Part` object to convert.
    :type part: :class:`music21.stream.Part`
    :param setts: A settings object.
    :type setts: :class:`settings.LilyPondSettings`

    :returns: The LilyPond-format notation for this part.
    :rtype: unicode string

    ** Extra Instruction **

    ``lily_instruction`` on the :class:`Part`
    """
    # Start the Part
    # We used to use some of the part's .bestName, but many scores (like
    # for **kern) don't have this.
    call_this_part = string_of_n_letters(8)
    while call_this_part in setts._parts_in_this_score:
        call_this_part = string_of_n_letters(8)
    setts._parts_in_this_score.append(call_this_part)
    post = [call_this_part, u" =\n{\n"]

    # If this part has the "lily_instruction" property set, this goes here
    if hasattr(part, 'lily_instruction'):
        post.append(part.lily_instruction)

    # If the part has a .bestName property set, we'll use it to generate
    # both the .instrumentName and .shortInstrumentName for LilyPond.
    instr_name = part.getInstrument().partName
    if instr_name is not None and len(instr_name) > 0:
        post.extend([u'\t%% ',
                     instr_name,
                     u'\n',u'\t\\set Staff.instrumentName = \\markup{ "',
                     instr_name,
                     u'" }\n',
                     u'\t\\set Staff.shortInstrumentName = \\markup{ "',
                     instr_name[:3],
                     u'." }\n'])
    elif hasattr(part, 'lily_analysis_voice') and part.lily_analysis_voice is True:
        setts._analysis_notation_parts.append(call_this_part)
        post.extend([u'\t%% vis annotated analysis\n', analysis_part_to_lily(part)])
    # Custom settings for bar numbers
    if setts.get_property('bar numbers') is not None:
        post.extend([u"\n\t\\override Score.BarNumber #'break-visibility = ",
                     setts.get_property('bar numbers'),
                     u'\n'])

    # If it's an analysis-annotation part, we'll handle this differently.
    if hasattr(part, 'lily_analysis_voice') and part.lily_analysis_voice is True:
        pass
    # Otherwise, it's hopefully just a regular, everyday Part.
    else:
        # What's in the Part?
        # TODO: break this into a separate method, process_part()
        # TODO: make this less stupid
        for thing in part:
            # Probably measures.
            if isinstance(thing, stream.Measure):
                if 0 == thing.number:
                    post.append(measure_to_lily(thing, True))
                else:
                    post.append(measure_to_lily(thing))
            elif isinstance(thing, instrument.Instrument):
                # We can safely ignore this (for now?) because we already dealt
                # with the part name earlier.
                pass
            elif isinstance(thing, tempo.MetronomeMark):
                # TODO: at some point, we'll have to deal with this nicely
                pass
            elif isinstance(thing, meter.TimeSignature):
                pass
            elif isinstance(thing, note.Note) or isinstance(thing, note.Rest):
                post.extend([note_to_lily(thing), u' '])
            # **kern importer garbage... well, it's only garbage to us
            elif isinstance(thing, humdrum.spineParser.MiscTandem):
                # http://mit.edu/music21/doc/html/moduleHumdrumSpineParser.html
                # Is there really nothing we can use this for? Seems like these
                # exist only to help music21 developers.
                pass
            else:
                pass
                #msg = u'Unknown object in Stream; type is %s.' % type(thing)
                #print(msg)  # DEBUG
                #raise UnidentifiedObjectError(msg + unicode(thing))
    # finally, to close the part, join, and return!
    post.append(u"}\n")
    return u''.join(post)


def stream_to_lily(the_stream, setts, the_index=None):
    """
    Convert a :class:`Stream` object into the LilyPond string.

    :param the_stream: The :class:`Stream` object to convert. Refer to "List of Supported Stream
        Objects" below.
    :type the_stream: :class:`music21.stream.Stream`
    :param setts: A settings object.
    :type setts: :class:`settings.LilyPondSettings`
    :param the_index: If this value is not ``None`` (the default), it is used in the return value.
        This is for use with multiprocessing. Refer to "Return Values" below.

    :returns: The LilyPond string, either by itself or in a 2- or 3-tuple. Refer to "Return Values"
        below.
    :rtype: unicode string or tuple

    :raises: :exc:`UnidentifiedObjectError` when ``the_stream`` is not one of the supported types.

    ** List of Supported Stream Objects **

    * :class:`music21.stream.Part` (or :class:`music21.stream.PartStaff`) (note: If ``the_stream``
        is a :class:`Part` and ``the_index`` is not ``None``, a 3-tuple will be returned.)
    * :class:`music21.stream.Score` (NOTE: not now!!!!!!!)
    * :class:`music21.metadata.Metadata`
    * :class:`music21.layout.StaffGroup`
    * :class:`music21.humdrum.spineParser.MiscTandem`
    * :class:`music21.humdrum.spineParser.SpineComment`
    * :class:`music21.humdrum.spineParser.GlobalComment`

    ** Special Attribute-Things **

    * ``lily_analysis_voice`` on a :class:`Part`.

    ** Return Values **

    * If ``index`` is ``None``, the return value is simply a unicode string.
    * If ``index`` is not ``None`` and ``the_stream`` is a :class:`Part`, a 3-tuple with the value
        of ``index``, the unicode string, and the 8-character unicode string used as the part name.
    * If ``index`` is not ``None`` but ``the_stream`` is not a :class:`Part`, a 2-tuple with the
        value of ``index`` and the unicode string.
    """
    if isinstance(the_stream, str):
        the_stream = converter.thawStr(the_stream)

    obj_type = type(the_stream)
    post = None
    part_name = None

    #if obj_type == stream.Score:
        #post = ScoreMaker(the_stream, setts).get_lilypond()
    if obj_type == stream.Part or obj_type == stream.PartStaff:
        post = part_to_lily(the_stream, setts)
        part_name = post[:8]
    elif obj_type == metadata.Metadata:
        post = metadata_to_lily(the_stream, setts)
    elif obj_type == layout.StaffGroup:
        # TODO: Figure out how to use this by reading documentation
        post = u''
    elif obj_type == humdrum.spineParser.MiscTandem:
        # http://mit.edu/music21/doc/html/moduleHumdrumSpineParser.html
        # Is there really nothing we can use this for? Seems like these exist only to help
        # the music21 developers.
        post = u''
    elif obj_type == humdrum.spineParser.GlobalReference:
        # http://mit.edu/music21/doc/html/moduleHumdrumSpineParser.html
        # These objects have lots of metadata, so they'd be pretty useful!
        post = u''
    elif obj_type == humdrum.spineParser.GlobalComment:
        # http://mit.edu/music21/doc/html/moduleHumdrumSpineParser.html
        # These objects have lots of metadata, so they'd be pretty useful!
        post = u''
    elif obj_type == layout.ScoreLayout:  # TODO: this (as in Lassus duos)
        post = u''
    elif obj_type == text.TextBox:  # TODO: this (as in Lassus duos)
        post = u''
    else:
        # Anything else, we don't know what it is!
        msg = u'Unknown object in Stream; type is %s.' % type(the_stream)  # DEBUG
        print(msg)  # DEBUG
        post = u''
        #raise UnidentifiedObjectError(msg)

    if the_index is not None and (obj_type == stream.Part or obj_type == stream.PartStaff):
        return (the_index, post, part_name)
    elif the_index is not None:
        return (the_index, post)
    else:
        return post

































