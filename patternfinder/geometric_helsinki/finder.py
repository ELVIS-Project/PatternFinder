from builtins import object # for python 2 & 3 custom iterator compatibility
from patternfinder.geometric_helsinki.NoteSegment import NotePointSet, CmpItQueue
from pprint import pformat # for logging
from fractions import Fraction # for scale verification
#from geometric_helsinki import DEFAULT_SETTINGS
#from geometric_helsinki.settings import DEFAULT_SETTINGS
from collections import namedtuple # for use in __repr__
from patternfinder.geometric_helsinki.occurrence import Occurrence
import algorithms
import copy # to copy excerpts from the score
import music21
import patternfinder.geometric_helsinki # Why isn't geometric_helsinki already present at top level namespace if Finder is imported?
import logging
import logging.config
import os
import yaml
import pdb

DEFAULT_SETTINGS = {
        'algorithm' : 'P1',
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


class ValidationError(Exception):
    def __init__(self, msg, key, arg, valid_options):
        self.message = "\n".join([
            msg + " \n",
            "Parameter '{0}' has value of {1}".format(key, arg),
            "Valid arguments are: {0}".format(e.message)])

class Finder(object):
    """
    Desired syntax:

        Finder()
        Finder.update(pattern='foo.krn', source='bar.krn') or
        Finder.update(foo.krn, bar.krn)

        Finder('pattern.krn', 'source.krn')

        Finder(source='bar.krn')
        Finder.update(pattern='foo.krn')

        When either source or pattern are unspecified, they should be NoneType, not a Stream

        @TODO update is broken for pattern / source changing. certain settings must be recalculated such as threshold and pattern window. maybe make these things functions of the length?
        @TODO put occurrences in a separate occurrence class, so we can do:
            for occ in finder:
                occ.colour_in_score()
        @TODO no measure info runs into errors because of occ excerpt writing. check for measure info!
        @TODO Delay creating the algorithm (or even pre processing) until you have both the pattern and the source! what's the point while one is None?
        @TODO P2 is broken - cannot find modules A1, A2, B1, and B2 in the Palestrina Kyrie movement
        @TODO with pointers, you can put a progress on the algorithm completion!
    """
    def __init__(self, pattern=None, source=None, **kwargs):
        """
        A Finder object is like an algorithm factory.
        Taking into account user-specified settings, it picks an algorithm
        and returns a generator to loop through all occurrences
        of the pattern within the source.

        >>> p = music21.converter.parse('tinynotation: 4/4 c4 e4')
        >>> s = music21.converter.parse('tinynotation: 4/4 c4 e4 c2 e2')
        >>> foo = Finder(p, s)
        >>> occ = next(foo) # occ is a list of InterNoteVectors
        >>> (occ[0].x, occ[0].y)
        (0.0, 0)

        >>> foo.update(scale=0.5)
        >>> next(foo)

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
        valid_options = ['P1', 'P2', 'P3', 'S1', 'S2', 'W1', 'W2']
        if arg in valid_options:
            return arg
        else:
            raise ValueError(valid_options)

    def _validate_threshold(self, arg):
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
        # @TODO validate colour
        valid_options = ['any hexadecimal RGB colour?']
        return arg





















    """
    1) THRESHOLD AND MISMATCHES

    # User-settings limitations (these limitations don't apply to default settings)
    # @TODO make threshold and mismatches define an upper/lower bound range of tolerance
    if ('threshold' in kwargs) and ('mismatches' in kwargs):
        raise ValueError("Threshold and mismatches not yet both supported: use one or the other")


    2) PARSE SCORES

    update()
    ### PARSE SCORES
    if 'pattern' in kwargs:
        self.pattern = self.parse_score(kwargs['pattern'])
        logger.debug("Parsed pattern")
        self.patternPointSet = NotePointSet(self.pattern)
        logger.debug("NotePointSet: Sorted and chord-flattened pattern")
    if 'source' in kwargs:
        self.source = self.parse_score(kwargs['source'])
        logger.debug("Parsed source")
        self.sourcePointSet = NotePointSet(self.source)
        logger.debug("NotePointSet: Sorted and chord-flattened source")


    def parse_score(self, file_or_stream):
        The input to Finder can be a symbolic music file or a music21 Stream

        We check before leaping rather than duck typing because the exceptions
        thrown by music21.converter.parse vary widely over many possible inputs

        Raises ValueError if input is neither an instance of str nor music21.stream.Stream
        logger = logging.getLogger("{0}.{1}".format(__name__, 'parse_scores'))

        # Check before you leap
        if isinstance(file_or_stream, str):
            score = music21.converter.parse(file_or_stream)
            score.derivation.origin = music21.ElementWrapper(file_or_stream)
            score.derivation.method = 'music21.converter.parse()'
        elif isinstance(file_or_stream, music21.stream.Stream):
            score = file_or_stream
            score.derivation.method = 'user input'
        # Allow for pattern or source to be None, which is the default value in Finder __init__()
        elif not file_or_stream:
            return
        else:
            raise ValueError("Invalid score input!"
                    + "{0} must be a file name (string) or music21 Stream.".format(file_or_stream))
        return score

    """


if __name__ == "__main__":
    import doctest
    doctest.testmod()
