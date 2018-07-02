import os
import yaml
import logging
import pdb

import music21

from pprint import pformat # for logging
from builtins import object # for python 2 & 3 custom iterator compatibility
from fractions import Fraction # for scale verification
from collections import namedtuple # for use in __repr__

#import patternfinder.geometric_helsinki.algorithms
from patternfinder.geometric_helsinki.algorithms import GeometricHelsinkiBaseAlgorithm
from patternfinder.geometric_helsinki.geometric_notes import NotePointSet
from patternfinder.geometric_helsinki.occurrence import GeometricHelsinkiOccurrence

## SETTINGS
DEFAULT_SETTINGS_PATH = 'patternfinder/geometric_helsinki/default_settings.yaml'

Param = namedtuple('Param', ['user', 'algorithm'])

def load_default_settings():
    """Loads default settings from yaml file. If path not found, uses a hard-coded dict"""
    if os.path.exists(DEFAULT_SETTINGS_PATH):
        with open(DEFAULT_SETTINGS_PATH, 'rt') as f:
            default_settings = yaml.safe_load(f.read())
    else:
        logging.getLogger(__name__).warning(DEFAULT_SETTINGS_PATH + "not found; we will use the hard-coded"
                + "dictionary stored in " + __name__ + " to determine the default settings")
        default_settings = {
                'algorithm' : 'auto',
                'pattern_window' : 1,
                'source_window' : 5,
                'scale' : 'pure',
                'threshold' : 'all',
                'mismatches' : 0,
                'interval_func' : 'semitones'}
    return default_settings

class Finder(object):
    """
    A python generator responsible for the execution of geometric helsinki algorithms


    Doctests
    ---------
    >>> import music21
    >>> import patternfinder.geometric_helsinki

    >>> p = music21.converter.parse('tinynotation: 4/4 c4 d4 e2')
    >>> s = music21.converter.parse('tinynotation: 4/4 c4 d4 e2')
    >>> p_in_s = my_finder(p, s)
    >>> next(p_in_s).notes == list(s.flat.notes)
    True
    """
    default_settings = load_default_settings()

    def __init__(self, pattern_input, source_input, **kwargs):
        """
        Input
        ------
        pattern: the query for which we are looking for in the source
            str filename pointing to a symbolic music file
            music21.stream.Stream
        source: the database of music in which we are looking for the pattern
            str filename pointing to a symbolic music file
            music21.stream.Stream
        settings: keyword arguments which choose the algorithm and manage its execution
            keyword arguments (like an unpacked dictionary)

        >>> import music21
        >>> import patternfinder.geometric_helsinki as gh
        >>> p = music21.converter.parse('tinynotation: 4/4 c4 e4 d4')
        >>> s = music21.converter.parse('tinynotation: 4/4 c4 e4 d4 r4 c2 e2 d2 r2 c#2 r2 e-1 r1 g1')
        >>> my_finder = gh.Finder(p, s)
        >>> occ = next(my_finder) # occ is an Occurrence object
        >>> occ.notes
        [<music21.note.Note F>, <music21.note.Note E>, <music21.note.Note D>]

        >>> next(gh.Finder(p, s, scale=2.0)).offset
        4.0

        >>> for occ in gh.Finder(music21.converter.parse('tinynotation: 4/4 c#4 e-4 g4'), s, scale='warped')
        ...     (occ.offset, occ.duration)
        (12.0, 8.0)
        """
        # Log creation of this object
        self.logger = logging.getLogger(__name__)
        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info("Creating Finder with: \npattern %s\n source %s\n settings \n%s",
                    pattern_input, source_input, pformat(kwargs))

        self._parse_scores(pattern_input, source_input)

        ## (2) SETTINGS (executed second, since some settings require the length of the note point sets)
        self.settings = {}
        self.settings['pattern'] = Param(pattern_input, self.patternPointSet)
        self.settings['source'] = Param(source_input, self.sourcePointSet)

        # Load the default settings, check their validity & translate them
        self.settings.update({key : Param('default', arg)
            for key, arg in self.process_and_translate(self.default_settings).items()})

        # Validate and translate user settings
        self.settings.update({key : Param(kwargs[key], arg)
            for key, arg in self.process_and_translate(kwargs).items()})

        ## (3) Get the algorithm
        self.algorithm = GeometricHelsinkiBaseAlgorithm.factory(
                self.settings['pattern'].algorithm,
                self.settings['source'].algorithm,
                {key : arg.algorithm for key, arg in self.settings.items()})

        # Instantiate the algorithm generator
        self.output = (GeometricHelsinkiOccurrence(self, 1, occ, self.source, self.sourcePointSet)
                       for occ in self.algorithm)

    def _parse_scores(self, pattern_input, source_input):
        """Defines self.pattern(PointSet) and self.source(PointSet)"""
        self.pattern = self.get_parameter_translator('pattern')(pattern_input)
        self.patternPointSet = NotePointSet(self.pattern)
        self.patternPointSet_offsetSort = NotePointSet(self.pattern, offsetSort=True)

        self.source = self.get_parameter_translator('source')(source_input)
        self.sourcePointSet = NotePointSet(self.source)
        self.sourcePointSet_offsetSort = NotePointSet(self.source, offsetSort=True)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.output)

    def __repr__(self):
        return "\n".join([
            super(Finder, self).__repr__(),
            "algorithm " + self.algorithm.__class__.__name__,
            "settings are.. \n {0}".format(self.__repr_settings__())])

    def __repr_settings__(self):
        """
        Output resembles yaml format

        For each keyword, we provide the user-specified input and its
        translation
        """
        output = ""
        for key in self.settings:
            output += ("\n" + key + ":"
                    + "\n    user:" + str(self.settings[key].user)
                    + "\n    algy:" + str(self.settings[key].algorithm))
        return output

    ## FINDER SETTINGS MANAGEMENT
    def process_and_translate(self, kwargs):
        """
        Validates user-specified or default-specified settings
        Translated keywords to algorithm-usable values

        Some parameters are validated and translated before being placed into the settings dict
        These validation and translation functions are stored as attributes of self as _'key'
        They either return the value or raise a ValueError with the valid options as the error message.
        """
        #@TODO threshold = 'all' iff pattern_window = 1 iff mismatches = 'min'

        # Log this function with a separate logger
        logger = logging.getLogger("{0}.{1}".format(__name__, 'process_settings'))

        processed_kwargs = {}
        for key, arg in kwargs.items():
            logger.debug("Processing setting %s with value %s", key, arg)
            # Check to see if all user-specified settings are defined in the default settings
            if key not in self.default_settings:
                raise ValueError("Parameter '{0}' is not a valid parameter.".format(key)
                        + "because it does not exist in the default settings.")
            # Validate and translate the paramter arguments
            try:
                processed_kwargs[key] = self.get_parameter_translator(key)(arg)
                logger.debug("'%s' : %s translates to %s", key, arg, processed_kwargs[key])
            except ValueError as e:
                raise ValueError("\n".join([
                    "Parameter '{0}' has value of {1}".format(key, arg),
                    "Valid arguments are: {0}".format(e.message)]))
        return processed_kwargs

    def get_parameter_translator(self, key):
        """
        Getter for the keyword validator functions
        If a keyword does not have a validator function, return the identity function
        """
        return getattr(self, '_validate_' + key, lambda p: p)

    def _validate_pattern(self, file_or_stream):
        """
        The input to Finder can be a symbolic music file or a music21 Stream

        We check before leaping rather than duck typing because the exceptions
        thrown by music21.converter.parse vary widely over many possible inputs
        """
        valid_options = []

        valid_options.append("str (symbolic music filename)")
        if isinstance(file_or_stream, str):
            score = music21.converter.parse(file_or_stream)
            score.derivation.origin = music21.ElementWrapper(file_or_stream)
            score.derivation.method = 'music21.converter.parse()'
            return score

        valid_options.append("music21.stream.Stream")
        if isinstance(file_or_stream, music21.stream.Stream):
            score = file_or_stream
            score.derivation.method = 'user input'
            return score

        # Allow for pattern or source to be None, which is the default value in Finder __init__()
        valid_options.append("None")
        if not file_or_stream:
            return

        raise ValueError(valid_options)

    def _validate_source(self, arg):
        return self.get_parameter_translator('pattern')(arg)

    def _validate_algorithm(self, arg):
        """
        Validates and translates the 'algorithm' parameter
        """
        valid_options = ['P1', 'P2', 'P3', 'S1', 'S2', 'W1', 'W2', 'auto']
        if arg in valid_options:
            return arg
        else:
            raise ValueError(valid_options)

    def _validate_threshold(self, arg):
        """
        Threshold defines the number of pattern notes which must be incorporated
        into any returned occurrence

        Options:
            'all'
                every pattern note has to be found
            int x
                at least x notes must be found
            0 < p < 1
                at least p (as a percentage) notes must be found
        """
        valid_options = ['all', 'positive_integer > 0', 'percentage 0 <= p <= 1', 'max']

        if arg == 'all':
            return len(self.patternPointSet)

        if isinstance(arg, int) and (arg > 0):
            if arg > len(self.patternPointSet):
                raise ValueError("Threshold cannot be greater than length of the pattern")
            return arg

        if isinstance(arg, float) and (arg >= 0) and (arg <= 1):
            from math import ceil
            return int(ceil(len(self.patternPointSet) * arg))

        if arg == 'max':
            raise ValueError("Threshold option 'max' not yet implemented")

        raise ValueError(valid_options)

    def _validate_mismatches(self, arg):
        """
        Symmetrical to threshold
        """
        valid_options = []
        error = ""

        valid_options.append('0 <= positive integer <= pattern length')
        if isinstance(arg, int) and (arg >= 0) and (arg <= len(self.patternPointSet)):
            return arg

        valid_options.append('percentage 0 <= p <= 1')
        if isinstance(arg, float) and (arg >= 0) and (arg <= 1):
            from math import ceil
            return int(ceil(len(self.patternPointSet) * arg))

        valid_options.append('min')
        if arg == 'max':
            raise ValueError("Mismatches option 'min' not yet implemented")

        raise ValueError(valid_options)

    def _validate_scale(self, arg):
        """
        Scale determines the time-scaling liberties used by the algorithms to find
        an occurrence of the pattern within the source

        Segregates the algorithms into three classes: (P)ure, (S)caled, (W)arped
        """
        valid_options = []

        ## Integer input
        valid_options.append('2-tuple of positive integers (numerator, denominator)')
        try:
            scale = Fraction(*arg)
        except (TypeError, ValueError):
            valid_options.append('integer or float >= 0')
            try:
                scale = Fraction(arg)
            except ValueError:
                pass

        ## String Keywords
        string_kwargs = {
                'pure' : 1,
                'any' : arg,
                'warped' : arg}
        valid_options.extend(string_kwargs.keys())

        try:
            return string_kwargs[arg]
        except KeyError:
            if isinstance(scale, Fraction) and scale >= 0:
                return scale
            else:
                raise ValueError(valid_options)

    def _validate_pattern_window(self, arg):
        valid_options = []

        valid_options.append('positive integer > 0')
        if isinstance(arg, int) and (arg > 0):
            return arg

        raise ValueError(valid_options)

    def _validate_source_window(self, arg):
        return self.get_parameter_translator('pattern_window')(arg)

    def _validate_interval_func(self, arg):
        valid_options = {
                'semitones' : lambda v: v.chromatic.semitones,
                # 4 -> 4, 13 -> 1, -13 -> -1, -11 -> -11
                'semitones-mod12' : lambda v: (
                    (v.chromatic.semitones % 12) if v.chromatic.semitones > 0
                    else -(-v.chromatic.semitones % 12)),
                'generic' : lambda v: v.generic.value,
                'base40' : lambda v: (
                    music21.musedata.base40.pitchToBase40(v.noteEnd) -
                    music21.musedata.base40.pitchToBase40(v.noteStart))}
        try:
            return valid_options[arg]
        except KeyError:
            raise ValueError(valid_options.keys())

    def _validate_colour(self, arg):
        #@TODO validate colour issue #17
        return arg

if __name__ == "__main__":
    import doctest
    doctest.testmod()
