from geometric_algorithms.geo_algorithms import DEFAULT_SETTINGS
from builtins import object
import geometric_algorithms

class Finder(object):
    def __init__(self, pattern, source, **kwargs):
        # Update the default settings with user-specified ones so that the user only has to specify non-default parameters.
        settings = {key : val for key, val in DEFAULT_SETTINGS.items()}
        settings.update(kwargs)

        if settings['scale'] == 1 or settings['scale'] == 'pure':
            cls = 'P'
        elif settings['scale'] == 'warped':
            cls = 'W'
        else:
            cls = 'S'

        if settings['threshold'] == 'all':
            tp = '1'
        else:
            tp = '2'

        if settings['algorithm']:
            algorithm_name = settings['algorithm']
        else:
            algorithm_name = cls + tp

        algorithm = getattr(geometric_algorithms, algorithm_name)
        self.algorithm = algorithm(pattern, source, **kwargs)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.algorithm)
