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
from patternfinder.geometric_helsinki.GeometricNotes import NotePointSet
from patternfinder.geometric_helsinki.occurrence import Occurrence

## SETTINGS
DEFAULT_SETTINGS_PATH = 'patternfinder/geometric_helsinki/default_settings.yaml'

## Load default settings
if os.path.exists(DEFAULT_SETTINGS_PATH):
    with open(DEFAULT_SETTINGS_PATH, 'rt') as f:
        DEFAULT_SETTINGS = yaml.safe_load(f.read())
else:
    logging.getLogger(__name__).warning(DEFAULT_SETTINGS_PATH + "not found; we will use the hard-coded"
            + "dictionary stored in " + __name__ + " to determine the default settings")
    DEFAULT_SETTINGS = {
            'algorithm' : 'auto',
            'pattern_window' : 1,
            'source_window' : 5,
            'scale' : 'pure',
            'threshold' : 'all',
            'mismatches' : 0,
            'interval_func' : 'semitones',
            'colour' : 'red',
            'modify_source' : False,
            'show_pattern' : False,
            'excerpt' : True,
            'auto_select' : True,
            'pattern' : None,
            'source' : None,
            'load_defaults' : False}

class Finder(object):
    """
    A python generator responsible for the execution of geometric helsinki algorithms

    Doctests
    ---------
    >>> import music21
    >>> import patternfinder.geometric_helsinki as helsinki
    >>> my_finder = helsinki.Finder()

    >>> p = music21.converter.parse('tinynotation: 4/4 c4 d4 e2')
    >>> my_finder.update(pattern=p)

    >>> s = music21.converter.parse('tinynotation: 4/4 c4 d4 e2')
    >>> my_finder.update(source=s)

    >>> next(my_finder).offset
    0.0
    """
    def __init__(self, pattern=None, source=None, **kwargs):
        """
        Input (optional - can be initialized with nothing)
        ------
        pattern: the query for which we are looking for in the source
            str filename pointing to a symbolic music file
            music21.stream.Stream
        source: the database of music in which we are looking for the pattern
            str filename pointing to a symbolic music file
            music21.stream.Stream
        settings: keyword arguments which choose the algorithm and manage its execution
            keyword arguments (like an unpacked dictionary)

        Output
        ------
        python generator which yields Occurrence objects

        >>> import music21
        >>> import patternfinder.geometric_helsinki as helsinki
        >>> p = music21.converter.parse('tinynotation: 4/4 c4 e4')
        >>> s = music21.converter.parse('tinynotation: 4/4 c4 e4 r2 c2 e2 c2 r2 e1')
        >>> my_finder = helsinki.Finder(p, s)
        >>> occ = next(my_finder) # occ is an Occurrence object
        >>> occ.measure_range
        [1]

        >>> my_finder.update(scale=2)
        >>> next(my_finder).measure_range
        [2]

        >>> my_finder.update(scale='warped')
        >>> for occ in my_finder:
        ...     occ.measure_range
        [1]
        [1, 2]
        [1, 2, 3]
        [2]
        [2, 3, 4]
        [3, 4]
        """
        # Log creation of this object
        self.logger = logging.getLogger(__name__)
        self.logger.info("Creating Finder with: \npattern %s\n source %s\n settings \n%s",
                pattern, source, pformat(kwargs))

        self.settings = {key : namedtuple("Param", ['user', 'algorithm'])._make((arg, None))
                for key, arg in DEFAULT_SETTINGS.items()}

        # Load default settings in the update() function because some settings require
        # parsed scores in order to process
        self.update(pattern=pattern, source=source, **kwargs)

    def __iter__(self):
        """
        Built-in python function for iterators
        """
        return self

    def __next__(self):
        """
        Built-in python function for iterators
        """
        return next(self.output)

    def __repr__(self):
        return "\n".join([
            self.algorithm.__class__.__name__,
            # @TODO eat up the derivation chain to find the file name input?
            "pattern = {0}".format(self.pattern),
            "source = {0}".format(self.source),
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

    def update(self, *args, **kwargs):
        """
        Runs all necessary pre-processing common to every algorithm
        (lexicographic sorting and chord flattening)

        Logs before and after functions within workflow.

        Usage:

        Can initialize with nothing; update with just the source, or just the pattern
        >>> from tests.test_lemstrom_example import LEM_PATH_PATTERN, LEM_PATH_SOURCE
        >>> foo = Finder()
        >>> foo.update(source=LEM_PATH_PATTERN('a'))

        Remember all user settings until the defaults are restored
        >>> foo.update(threshold=1)
        >>> foo.update() # Shouldn't change anything
        >>> foo.settings['threshold']
        Param(user=1, algorithm=1)

        Set up settings before importing pattern or source
        >>> foo = Finder(threshold='all')
        >>> foo.settings['threshold']
        Param(user='all', algorithm=0)

        Threshold will be recalculated based on the new pattern
        >>> foo.update(pattern=LEM_PATH_PATTERN('a'))
        >>> foo.settings['threshold']
        Param(user='all', algorithm=6)

        Load defaults - use args rather than kwargs. Loading defaults should be
        a one-time operation rather than a repeated action taken at every update
        >>> foo.update(threshold=4)
        >>> foo.update('load_defaults')
        >>> foo.settings['threshold'].algorithm
        6
        """
        # Log this method with a separate logger
        logger = logging.getLogger("{0}.{1}".format(self.logger.name, 'update'))
        logger.info('Updating Finder with settings \n%s', pformat(kwargs))

        ## (1) PARSE SCORES only if they are present in this round of kwargs
        for score in (s for s in ('pattern', 'source') if s in kwargs):
            setattr(self, score, self.get_parameter_translator(score)(kwargs[score]))
            setattr(self, score + 'PointSet', NotePointSet(getattr(self, score)))

        # Stop here until the user re-updates with both the pattern and the source
        if self.pattern is None or self.source is None:
            return

        ## (2) PROCESS SETTINGS
        logger.debug("Processing user settings...")

        if 'load_defaults' in args:
            previous_settings = dict(DEFAULT_SETTINGS)
        else:
            previous_settings = {key : arg.user for key, arg in self.settings.items()}

        # Merge the new input with previous user input (principally initialized with defaults)
        previous_settings.update(kwargs)
        # Will raise ValueError if erroneous input
        processed_settings = self.process_and_translate(previous_settings)
        # No error was thrown. Store the new input and its algorithm translation
        self.settings.update({key : arg._replace(user=previous_settings[key], algorithm=processed_settings[key])
            for key, arg in self.settings.items()})

        logger.debug("Processed internal settings are: \n %s",
                self.__repr_settings__())

        ## (3) SELECT THE ALGORITHM
        # Allow the user to manually choose the algorithm rather than letting
        # the system choose the fastest one based on the settings input
        self.algorithm = GeometricHelsinkiBaseAlgorithm.factory(
                self.patternPointSet,
                self.sourcePointSet,
                {key : arg.algorithm for key, arg in self.settings.items()})

        ## (4) RUN THE ALGORITHM
        self.algorithm.pre_process()
        self.results = self.algorithm.filtered_results()
        self.occurrences = self.algorithm.occurrence_generator()

        # (5) OUTPUT STUFF!
        self.output = self.output_generator()

    def output_generator(self):
        for occ in self.occurrences:
            self.logger.info("Yielded {0}".format(occ))
            #yield self.process_occurrence(occ)
            yield Occurrence(occ)

    def process_occurrence(self, occ, ):
        """
        Given an occurrence, process it and produce output

        Implementation:
        We look at the original source and gather all of the notes which have been matched.
        First we tag these matched notes them with a group. We use groups rather than id's because
        music21 will soon implement group-based style functions.
        Next, we deepcopy the measure range excerpt in the score corresponding to matched notes
        Finally we untag the matched notes in the original score and output the excerpt

        """

        return occ
















    def process_and_translate(self, kwargs):
        """
        Validates user-specified or default-specified settings
        Translated keywords to algorithm-usable values

        Some parameters are validated and translated before being placed into the settings dict
        These validation and translation functions are stored as attributes of self as _'key'
        They either return the value or raise a ValueError with the valid options as the error message.
        """
        # Log this function with a separate logger
        logger = logging.getLogger("{0}.{1}".format(__name__, 'process_settings'))

        processed_kwargs = {}
        for key, arg in kwargs.items():
            logger.debug("Processing setting %s with value %s", key, arg)
            # Check to see if all user-specified settings are defined in the default settings
            if key not in DEFAULT_SETTINGS:
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
        valid_options = []

        valid_options.append('all')
        if arg == 'all':
            return len(self.patternPointSet)

        valid_options.append('positive integer > 0')
        if isinstance(arg, int) and (arg > 0):
            return arg

        valid_options.append('percentage 0 <= p <= 1')
        if isinstance(arg, float) and (arg <= 1):
            from math import ceil
            return int(ceil(len(self.patternPointSet) * arg))

        valid_options.append('max')
        if arg == 'max':
            raise ValueError("Threshold option 'max' not yet implemented")

        raise ValueError(valid_options)

    def _validate_mismatches(self, arg):
        valid_options = []

        valid_options.append('positive integer >= 0')
        if isinstance(arg, int) and (arg >= 0):
            return arg

        raise ValueError(valid_options)

    def _validate_scale(self, arg):
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
        # @TODO validate colour - check valid string values
        # xml takes hexadecimal colours, lilypond does not
        valid_options = ['any hexadecimal RGB colour?']
        return arg

""""
Not used but would potentially make the code a lot cleaner
class ValidationError(Exception):
    def __init__(self, msg, key, arg, valid_options):
        self.message = "\n".join([
            msg + " \n",
            "Parameter '{0}' has value of {1}".format(key, arg),
            "Valid arguments are: {0}".format(e.message)])
"""

if __name__ == "__main__":
    import doctest
    doctest.testmod()
