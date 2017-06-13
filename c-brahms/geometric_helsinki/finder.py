from builtins import object # for python 2 & 3 custom iterator compatibility
from geometric_helsinki.NoteSegment import NotePointSet
from pprint import pformat # for logging
from fractions import Fraction # for scale verification
import copy # to copy excerpts from the score
import music21
import geometric_helsinki
import logging
import logging.config
import os
import yaml
import pdb

## @TODO these should be put in the __init__ file I think
LOGGING_PATH = 'geometric_helsinki/logging.yaml'
OUTPUT_PATH = 'music_files/music21_temp_output'

def update_logging_config():
    """
    Configures logging from a logging.yaml file
    This is only run within object creation, and not on import, so that
    if the user is importing other librairies with logging which set
    disable_previous_loggers to True, then the logging here will still work.
    """
    if os.path.exists(LOGGING_PATH):
        with open(LOGGING_PATH, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO)

# Music21 User Settings
us = music21.environment.UserSettings()
us['directoryScratch'] = 'music_files/music21_temp_output'

"""
And maybe this would work better if it could access the _key function which raised it?
class ValidationError(Exception):
    def __init__(self, msg, key, arg, valid_options):
        self.message = "\n".join([
            msg + " \n",
            "Parameter '{0}' has value of {1}".format(key, arg),
            "Valid arguments are: {0}".format(e.message)])
    pass
"""

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
    """
    def __init__(self, pattern_input=music21.stream.Stream(), source_input=music21.stream.Stream(), **kwargs):
        """
        An algorithm object parses the input and runs algorithm pre processing on __init__
        The object itself is a generator, so it won't begin looking for results until
        the user calls next(self)
        """
        # Set up logging
        update_logging_config()

        # Log creation of this object
        self.logger = logging.getLogger(__name__)
        self.logger.info('Creating Finder with:\n pattern %s\n source %s\n settings %s',
                pattern_input, source_input, pformat(kwargs))

        self.update('load_defaults', pattern=pattern_input, source=source_input, **kwargs)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.output)

    def decide_algorithm(self, settings):
        # Don't need keyword 'pure' since settings are processed first
        if settings['scale'] == 1:
            cls = 'P'
        elif settings['scale'] == 'warped':
            cls = 'W'
        else:
            cls = 'S'

        if ((settings['threshold'] == len(self.patternPointSet))
                and (settings['mismatches'] == 0)):
            tp = '1'
        else:
            tp = '2'

        return cls + tp

    def update(self, *args, **kwargs):
        """
        Update algorithm

        Logs before and after functions within workflow. Alternatively we could add loggers
        within each function context and log there instead? But then we'd need to do every
        instance of the functions as they are inherited in child classes...

        Also runs all necessary pre-processing common to every algorithm
        (lexicographic sorting and chord flattening)

        Usage:

        Change just pattern or source
        >>> foo = Finder()
        >>> foo.update(pattern=music21.stream.Stream())

        Remember the settings
        >>> foo = Finder()
        >>> foo.update(threshold=1)
        >>> foo.update()
        >>> foo.settings['threshold']
        1
        """
        # Log this method
        logger = logging.getLogger("{0}.{1}".format(self.logger.name, 'update'))
        logger.debug('Updating Finder with settings \n%s', pformat(kwargs))

        # User-settings limitations (these limitations don't apply to default settings)
        # @TODO make threshold and mismatches define an upper/lower bound range of tolerance
        if ('threshold' in kwargs) and ('mismatches' in kwargs):
            raise ValueError("Threshold and mismatches not yet both supported: use one or the other")

        ## PARSE THE SCORES
        # @TODO wrap in a function?
        if 'pattern' in kwargs:
            logger.debug("Attempting to parse the pattern...")
            self.patternPointSet = NotePointSet(kwargs['pattern'])
            self.patternPointSet.id = 'pattern'
            #self.patternPointer = (n for n in self.patternPointSet)
            logger.debug("Parsed the pattern")
        if 'source' in kwargs:
            logger.debug("Attempting to parse the source...")
            self.sourcePointSet = NotePointSet(kwargs['source'])
            self.sourcePointSet.id = 'source'
            #self.sourcePointer = (n for n in self.sourcePointSet)
            # @TODO come up with a better way to sort than this, srsly...
            self.sourcePointSet_offsetSort = NotePointSet(self.sourcePointSet, offsetSort=True)
            #self.sourcePointer_offsetSort = (n for n in self.sourcePointSet_offsetSort)
            logger.debug("Parsed the source")

        ### PROCESS SETTINGS
        logger.debug("Processing user settings")

        # Always call self.load_default_settings() when called from __init__()
        if 'load_defaults' in args:
            # Resets self.default_settings to {}
            # Sets self.settings to a processed DEFAULT_SETTINGS
            self.load_default_settings()
        self.user_settings.update(kwargs)

        # Validates and translates kwargs while updating self.settings
        self.settings.update(self.process_settings(kwargs))
        logger.info("Processed internal settings are: \n %s",
                pformat(self.settings))

        ## SELECT THE ALGORITHM
        # Allow the user to manually choose the algorithm rather than letting
        # the system choose the fastest one based on the settings input
        if not self.settings['auto_select']:
            algorithm_name = self.settings['algorithm']
        else:
            algorithm_name = self.decide_algorithm(self.settings)

        # @TODO do i need to use getattr here? on the module? whatabout self?
        algorithm = getattr(geometric_helsinki, algorithm_name)
        self.algorithm = algorithm(self.patternPointSet, self.sourcePointSet, self.settings)
        self.logger = logging.getLogger("{0}.{1}".format('geometric_algorithms', algorithm_name))

        ## RUN THE ALGORITHM
        self.results = self.algorithm.filtered_results()
        self.occurrences = self.algorithm.occurrence_generator()
        self.algorithm.pre_process()

        # OUTPUT STUFF!
        self.output = (self.process_occurrence(occ) for occ in self.occurrences)

    def load_default_settings(self):
        """
        Resets the Finder's settings to default settings and processes them
        Also dumps the saved user_settings up to this point

        >>> foo = Finder()
        >>> bar = Finder(algorithm='S2')

        >>> bar.user_settings['algorithm']
        'S2'
        >>> foo.settings == bar.settings
        False

        >>> bar.load_default_settings()
        >>> bar.user_settings
        {}
        >>> foo.settings == bar.settings # Fails because _interval_func generates a new lambda exp each time
        True

        """
        self.user_settings = {}
        self.settings = dict(DEFAULT_SETTINGS)
        try:
            self.settings.update(self.process_settings(DEFAULT_SETTINGS))
        except ValueError as e:
            message = "The default settings has an invalid argument. \n" + e.message
            raise ValueError(message)

    def process_settings(self, kwargs):
        """
        Validates user-specified settings (AND validates the default settings)
        Translated keywords to algorithm-usable values
        e.g. 'threshold' = 'all' --> threshold = len(pattern)

        Some parameters are validated and translated before put into the settings dict
        These validation and translation functions are stored as attributes of self as _'key'
        They either return the value or raise a ValueError with the valid options
        """
        # Log this function
        logger = logging.getLogger("{0}.{1}".format(__name__, 'process_settings'))

        processed_kwargs = {}

        ## VALIDATE KWARG KEYS
        for key in kwargs.keys():
            if key not in DEFAULT_SETTINGS.keys():
                raise ValueError("Parameter '{0}' is not a valid parameter.".format(key))

        ## VALIDATE AND TRANSLATE KWARGS
        # @TODO wrap the validation into a general function and turn the setting
        # processing into a dictionary comprehension
        for key, arg in kwargs.items():
            logger.debug("Processing setting %s with value %s", key, arg)
            # GET THE TRANSLATOR
            if hasattr(self, '_' + key):
                translator = getattr(self, '_' + key)
            else:
                # Default validator: does the key exist in the default settings?
                if key not in DEFAULT_SETTINGS:
                    raise ValueError("Parameter '{0}' is not a valid parameter ".format(key)
                        + "because it does not exist in the default settings.")
                logger.debug("'%s' does not have a validator/translator", key)
                processed_kwargs.update([(key, arg)])
                continue
            # VALIDATE & TRANSLATE THE DATA
            try:
                logger.debug("Validating and translating key %s ...", key)
                translation = translator(arg)
                processed_kwargs.update([(key, translation)])
                logger.debug("'%s' : %s translates to %s", key, arg, translation)
            except ValueError as e:
                # @TODO create a ValidationError to clean up this try catch. The error
                # could just be thrown directly in the translator
                message = "\n".join([
                "process_settings() has found an invalid argument. \n",
                "Parameter '{0}' has value of {1}".format(key, arg),
                "Valid arguments are: {0}".format(e.message)])
                raise ValueError(message)

        # @TODO make this better
        if 'threshold' in kwargs:
            self.settings['mismatches'] = (
                    len(self.patternPointSet) - processed_kwargs['threshold'])
        elif 'mismatches' in kwargs:
            self.settings['threshold'] = (
                    len(self.patternPointSet) - processed_kwargs['mismatches'])

        return processed_kwargs

    def process_occurrence(self, occ):
        """
        Given an occurrence, process it and produce output

        Implementation:
        We look at the original source and gather all of the notes which have been matched.
        First we tag these matched notes them with a group. We use groups rather than id's because
        music21 will soon implement group-based style functions.
        Next, we deepcopy the measure range excerpt in the score corresponding to matched notes
        Finally we untag the matched notes in the original score and output the excerpt
        """
        # Check if there's a score to colour
        if not self.sourcePointSet.derivation.origin:
            self.logger.info("Manual input: no original score to colour")
            return occ

        # @TODO colour pattern notes too
        # Each source note is either original or came from a chord, so 
        # we check the derivation to see which one to take.
        source_notes = [vec.noteEnd if not vec.noteEnd.derivation.origin
                else vec.noteEnd.derivation.origin for vec in occ]

        # Tag the source notes
        for note in source_notes:
            note.groups.append('occurrence')

        # Get a copied excerpt of the score
        first_measure_num = source_notes[0].getContextByClass('Measure').number
        last_measure_num = source_notes[-1].getContextByClass('Measure').number
        if self.settings['excerpt']:
            result = copy.deepcopy(self.sourcePointSet.derivation.origin.measures(
                    numberStart = first_measure_num,
                    numberEnd = last_measure_num))
        else:
            result = copy.deepcopy(self.sourcePointSet.derivation.origin)

        # Untag the matched notes, process the occurrence
        for excerpt_note in result.flat.getElementsByGroup('occurrence'):
            excerpt_note.color = self.settings['colour']
            if self.settings['colour_source']:
                excerpt_note.derivation.origin.color = self.settings['colour']
            else:
                excerpt_note.derivation.origin.groups.remove('occurrence')

        # Output the occurrence
        if self.settings['show_pattern'] and self.patternPointSet.derivation.origin:
            # @TODO output the pattern from a pointset if that's the only input we have
            output = music21.stream.Opus(
                    [self.patternPointSet.derivation.origin, result])
        else:
            output = result
        output.metadata = music21.metadata.Metadata()
        output.metadata.title = (
                "Transposed by " + str(occ[0].diatonic.simpleNiceName) +
                # XML and Lily output don't seem to preserve the measure numbers
                # even though you can see them in .show('t')
                " mm. {0} - {1}".format(first_measure_num, last_measure_num))

        output.matching_pairs = occ

        #Save the pdf file as wtc-i-##_alg.pdf
        #temp_file = output.write('lily')
        # rename tmp.ly.pdf to file_name_base.pdf
        #os.rename(temp_file, ".".join(['output', 'pdf']))
        # rename tmp.ly to file_name_base.ly
        #os.rename(temp_file[:-4], ".".join(['output', 'ly']))

        return output

    def _algorithm(self, arg):
        valid_options = ['P1', 'P2', 'P3', 'S1', 'S2', 'W1', 'W2']
        if arg in valid_options:
            return arg
        else:
            raise ValueError(valid_options)

    def _threshold(self, arg):
        valid_options = []

        # @TODO support using both threshold and mismatch as a range - DOESNT WORK
        if self.settings['mismatches'] > 0:
            return len(self.patternPointSet) - self.settings['mismatches']

        valid_options.append('all')
        if arg == 'all':
            return len(self.patternPointSet)

        valid_options.append('positive integer > 0')
        if isinstance(arg, int) and (arg > 0):
            return arg

        valid_options.append('max')
        if arg == 'max':
            raise ValueError("Threshold option 'max' not yet implemented")

        raise ValueError(valid_options)

    def _mismatches(self, arg):
        valid_options = []

        valid_options.append('positive integer >= 0')
        if isinstance(arg, int) and (arg >= 0):
            return arg

        raise ValueError(valid_options)

    def _scale(self, arg):
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


        """
        valid_options.append('pure')
        if arg == 'pure': return 1
        valid_options.extend(['any', 'warped'])
        if arg == 'any' or arg == 'warped': return arg

        if scale >= 0:
            return scale

        raise ValueError(valid_options)
        """
        try:
            return string_kwargs[arg]
        except KeyError:
            if isinstance(scale, Fraction) and scale >= 0:
                return scale
            else:
                raise ValueError(valid_options)


    def _pattern_window(self, arg):
        valid_options = []

        valid_options.append('positive integer > 0')
        if isinstance(arg, int) and (arg > 0):
            return arg

        raise ValueError(valid_options)

    def _source_window(self, arg):
        return self._pattern_window(arg)

    def _interval_func(self, arg):
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

    def _colour(self, arg):
        # @TODO validate colour
        valid_options = ['any hexadecimal RGB colour?']
        return arg

    def __repr__(self):
        return "\n".join([
            self.algorithm.__class__.__name__,
            # @TODO eat up the derivation chain to find the file name input?
            "pattern = {0}".format(self.patternPointSet.derivation),
            "source = {0}".format(self.sourcePointSet.derivation),
            "user settings = {0}".format(self.user_settings),
            "settings = \n {0}".format(pformat(self.settings))])

if __name__ == "__main__":
    import doctest
    doctest.testmod()
