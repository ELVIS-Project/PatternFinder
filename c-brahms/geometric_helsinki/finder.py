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
        """
        # Log this method
        logger = logging.getLogger("{0}.{1}".format(self.logger.name, 'update'))
        logger.info('Updating Finder with settings %s', pformat(kwargs))

        ## PARSE THE SCORES
        if 'pattern' in kwargs:
            logger.info("Attempting to parse the pattern...")
            self.patternPointSet = NotePointSet(kwargs['pattern'])
            self.patternPointSet.id = 'pattern'
            logger.info("Parsed the pattern")
        if 'source' in kwargs:
            logger.info("Attempting to parse the source...")
            self.sourcePointSet = NotePointSet(kwargs['source'])
            self.sourcePointSet.id = 'source'
            logger.info("Parsed the source")

        ## PROCESS SETTINGS
        logger.info("Processing user settings")
        # Defines self.user_settings and self.settings
        self.process_settings(kwargs)
        if logger.isEnabledFor(logging.INFO):
            logger.info("Processed user settings")
        elif logger.isEnabledFor(logging.DEBUG):
            logger.debug("Processed user settings \n %s", pformat(self.settings))

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

    def process_settings(self, user_settings):
        """
        Validates user-specified settings (AND validates the default settings)
        Translated keywords to algorithm-usable values
        e.g. 'threshold' = 'all' --> threshold = len(pattern)

        Some parameters are validated and translated before put into the settings dict
        These validation and translation functions are stored as attributes of self as _'key'
        They either return the value or raise a ValueError with the valid options
        """
        # Log this function
        logger = logging.getLogger("{0}.{1}".format('geometric_algorithms', 'process_settings'))

        # Generate self.settings from the default settings
        self.settings = dict(DEFAULT_SETTINGS.items())
        self.user_settings = user_settings

        # Validate user KEYS
        for key in user_settings.keys():
            if key not in DEFAULT_SETTINGS.keys():
                raise ValueError("Parameter '{0}' is not a valid parameter.".format(key))

        # Validate and translate the setting arguments
        self.settings.update(user_settings)
        for key, arg in self.settings.items():
            logger.debug("Processing setting %s with value %s", key, arg)
            try:
                # GET THE TRANSLATOR
                translator = getattr(self, '_' + key)
            except AttributeError:
                logger.debug("'%s' does not have a validator/translator", key)
                # If the parameter doesn't have a validator or translator, let it be
                continue
            try:
                # VALIDATE OR TRANSLATE THE DATA
                logger.debug("Validating and translating key %s ...", key)
                self.settings[key] = translator(arg)
                logger.debug("'%s' : %s translates to %s", key, arg, self.settings[key])
            except ValueError as e:
                # Distinguish whether the invalid data came from the DEFAULT settings, 
                # or the user-specified ones
                if key in user_settings.keys():
                    message = "\n".join([
                    "Parameter '{0}' has an invalid value of {1}".format(key, arg),
                    "Valid arguments are: {0}".format(e.message)])
                else:
                    message = "\n".join([
                    "DEFAULT SETTINGS has set parameter '{0}' to an invalid value of {1}".format(key, arg),
                    "Valid arguments are: {0}".format(e.message)])
                raise ValueError(message)

        # @TODO make threshold and mismatches define an upper/lower bound range of tolerance
        if ('threshold' in user_settings) and ('mismatches' in user_settings):
            raise ValueError("Threshold and mismatches not yet both supported: use one or the other")

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
        # The notes in the score corresponding to this occurrence
        original_notes = [vec.noteEnd if not vec.noteEnd.derivation.origin
                else vec.noteEnd.derivation.origin for vec in occ]

        # Tag the matched notes
        for note in original_notes:
            note.groups.append('occurrence')

        # Get a copied excerpt of the score
        excerpt = copy.deepcopy(self.sourcePointSet.derivation.origin.measures(
                numberStart = original_notes[0].getContextByClass('Measure').number,
                numberEnd = original_notes[-1].getContextByClass('Measure').number))

        # Untag the matched notes, process the occurrence
        for original_note, excerpt_note in zip(original_notes, excerpt.flat.getElementsByGroup('occurrence')):
            excerpt_note.color = 'red'
            original_note.groups.remove('occurrence')

        # Output the occurrence
        if self.settings['show_pattern'] and self.patternPointSet.derivation.origin:
            # @TODO output the pattern from a pointset if that's the only input we have
            output = music21.stream.Opus(
                    [self.patternPointSet.derivation.origin, excerpt, self.sourcePointSet.derivation.origin])
        else:
            output = excerpt
        output.metadata = music21.metadata.Metadata()
        output.metadata.title = "Transposed by " + str(occ[0].y)

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
            "pattern = {0}".format(self.patternPointSet.derivation),
            "source = {0}".format(self.sourcePointSet.derivation),
            "user settings = {0}".format(self.user_settings),
            "settings = \n {0}".format(pformat(self.settings))])
