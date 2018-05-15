import music21
import copy
import pprint
import logging
import pdb

from collections import namedtuple

Pattern = namedtuple('Pattern', ['id', 'stream', 'color'])

class BaseFinder(object):
    """
    A python generator responsible for the execution of algorithms.
    Each family of algorithms has a Finder class which subclasses BaseFinder

    Finders operate on the music21.stream.Stream level.
    They are responsible for:
        - parsing file paths into music21 streams
        - processing music21 streams into algorithm-specific input
        - validating user-specified parameters and translating these into
        algorithm-usable values
        - creating an algorithm generator and passing along its output
    """
    # each algorithm family has different parameters, so we store their default
    # settings in their respective directories using yaml files
    # this should be overridden by subclasses
    default_settings = {}

    def __init__(self, pattern_input, source_input, **kwargs):
        self.logger = logging.getLogger(__name__)
        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info("Creating Finder with: \npattern %s\n source %s\n settings \n%s",
                    pattern, source, pformat(kwargs))

        # Defines self.pattern and self.source music21 streams
        self._parse_scores(pattern_input, source_input)

        self.settings = {}
        self.settings['pattern'] = Param(pattern_input, self.patternPointSet)
        self.settings['source'] = Param(source_input, self.sourcePointSet)
        # Load the default settings, check their validity & translate them
        self.settings.update({key : Param('default', arg)
            for key, arg in self.process_and_translate(self.default_settings).items()})

        # Validate and translate user settings
        self.settings.update({key : Param(kwargs[key], arg)
            for key, arg in self.process_and_translate(kwargs).items()})

        self.algorithm = self._algorithm_factory(
            self.settings['pattern'].algorithm,
            self.settings['source'].algorithm,
            {key : arg.algorithm for key, arg in self.settings.items()})

        # Instantiate the algorithm generator
        self.output = (GeometricHelsinkiOccurrence(self, 1, occ, self.source) for occ in self.algorithm)

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
        valid_options = ["str (symbolic music filename)", "music21.stream.Stream"]
        pattern = None

        if isinstance(file_or_stream, str):
            score = music21.converter.parse(file_or_stream)
            score.derivation.origin = music21.ElementWrapper(file_or_stream)
            score.derivation.method = 'music21.converter.parse()'
            pattern = score

        if isinstance(file_or_stream, music21.stream.Stream):
            score = file_or_stream
            score.derivation.method = 'user input'
            pattern = score

        if pattern is not None:
            self.pattern = pattern
            return pattern
        else:
            raise ValueError(valid_options)

    def _validate_source(self, arg):
        self.source = self.get_parameter_translator('pattern')(arg)
        return self.source

class BaseOccurrence(music21.base.Music21Object):
    """
    Definition of a musical occurrence in the PatternFinder library

    Each family of algorithms return occurrences that subclass this base class.
    This base class provides a common API for occurrence processing in PatternFinder;
    some algorithms may return more information (such as direct mappings between
    pattern and source notes, rather than just the source notes)

    Important attributes:
        score - in what music21 stream was this occurrence found?
        @TODO pattern - what were we looking for?
        notes - what are the specific notes which form this occurrence?
        offset - the starting offset of the first note in the occurrence
        duration - the note release offset of the final note in the occurrence
    """

    def __init__(self, generator, identifier, list_of_notes, score):
        start_offset, end_offset = (list_of_notes[0].getOffsetInHierarchy(score),
                list_of_notes[-1].getOffsetInHierarchy(score) + list_of_notes[-1].duration.quarterLength)

        # Init music21 object with an unpacked dictionary rather than kwargs
        # since 'id' is a reserved python keyword
        super(BaseOccurrence, self).__init__(**{
            'id' : identifier,
            'groups' : [],
            'duration' : music21.duration.Duration(end_offset - start_offset),
            # 'activeSite' : score, # can't set object active site to somewhere it does not belong
            'offset' : start_offset, #TODO buggy, is always set to 0
            'priority' : 0,
            # Will sites be computed automatically if I leave it out? There may be more contexts other than score
            #'sites' : score,
            'derivation' : music21.derivation.Derivation()})
            # Music21 doesn't have style or Editorial() attributes - incorrect documentation?
            # 'style' : music21.style.Style(), 
            #'editorial' : music21.editorial.Editorial()})

        self.offset = start_offset
        self.duration = music21.duration.Duration(end_offset - start_offset)

        self.derivation.method = generator
        self.derivation.origin = score
        self.notes = list_of_notes
        self.score = score

    def __repr__(self):
        return pprint.pformat(self.notes)

    def __eq__(self, other):
        return (self.notes == other.notes) and (self.score == other.score)

    def __ne__(self, other):
        return self.notes != other.notes

    def __iter__(self):
        return iter(self.notes)

    def get_excerpt(self, color='red', left_padding=0, right_padding=0):
        """
        Returns a Score object representing the excerpt of the score which contains this occurrence
        All notes in the score which form part of the occurrence will belong to the 'occurrence' group

        You don't want to do this for all occurrences since deepcopy takes way too much time. That's
        why we put this in a separate method rather than __init__

        Input
        -------
        self - Occurrence object with notes and an associated score
        color - keyword color to color in the occurrence notes in this excerpt
        left_padding - an integer number of measures to include to the excerpt on the left side
        right_padding - an integer number of measures to include to the excerpt on the right side

        Raises
        -------
        StreamException if self.score has no measure information for the first or last notes
        """
        # beatAndMeasureFromOffset() will raise a StreamException if self.score has no measure info
        _beat, start_measure = self.score.beatAndMeasureFromOffset(self.offset)
        # Minus 1, otherwise the last note will push the offset out of bounds
        _beat, end_measure = self.score.beatAndMeasureFromOffset(self.offset + self.duration.quarterLength - 1)

        # Get a deepcopy excerpt of the score so post-processing will not modify original score
        # deepcopied music21Objects store their original parents in a derivation attribute
        excerpt = copy.deepcopy(self.score.measures(
                numberStart = start_measure.number - left_padding,
                numberEnd = end_measure.number + right_padding))

        # Tag the occurrence notes in the excerpt
        for note in excerpt.flat.notes:
            if note.derivation.origin.id in (obj.id for obj in self.source_notes):
                # music21 will soon implement group-based style functions
                note.groups.append('occurrence')
                note.style.color = color

        # @TODO
        # XML and Lily output don't seem to preserve the measure numbers
        # even though you can see them in stream.show('t')
        # Quick fix: put measure numbers in the excerpt title
        excerpt.metadata = music21.metadata.Metadata()
        excerpt.metadata.title = (" mm. {0} - {1}".format(
            start_measure.number, end_measure.number))

        return excerpt
