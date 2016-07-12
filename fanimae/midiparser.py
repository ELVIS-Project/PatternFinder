import music21
import pandas
from math import log
from vis.analyzers.indexers import noterest, interval, metre


def ioi_contour(durations):
    '''Translate offset intervals into letters.'''

    result = ''

    for c in range(len(durations) - 1):
        now = durations[c + 1]
        prev = durations[c]

        if prev > 0:
            ratio = log(now / prev) / log(2)
            if abs(ratio) < 1:
                e = 'R'
            elif 1 <= ratio and ratio < 2:
                e = 'l'
            elif 2 <= ratio:
                e = 'L'
            elif -2 < ratio and ratio <= -1:
                e = 's'
            else:
                e = 'S'
            result = result + e
        else:
            e = 'S'
            result = result + e

    return result


def directed_mod12(pitches):
    '''Translate intervals into symbols.'''

    symbols = ['a', 'b', 'c', 'd', 'e', 'f',
               'g', 'h', 'i', 'j', 'k', 'l', 'm',
               'n', 'o', 'p', 'q', 'r', 's',
               't', 'u', 'v', 'w', 'x', 'y']

    result = ''
    for c in range(len(pitches) - 1):
        intvl = int(pitches[c])
        if intvl >= 0 and intvl <= 12:
            result = result + symbols[intvl]
        else:
            intvl = abs(intvl) + 12
            result = result + symbols[intvl]

    return result


def to_midi(name):
    '''Translate note names into midi pitches.'''

    c = music21.pitch.Pitch(name)
    return c.midi


def process_file(filename):
    '''Parse the file and load it in with VIS.'''

    score = music21.converter.parse(filename)
    notes = noterest.NoteRestIndexer(score).run()

    all_iois = []
    all_intvls = []

    for part in notes:
        settings = {'compound or simple': 'simple', 'quality': 'chromatic'}
        intvls = interval.HorizontalIntervalIndexer(notes, settings).run()
        intervals = intvls['interval.HorizontalIntervalIndexer', part[1]]
        intervals = intervals.dropna().tolist()
        notes1 = notes[part]
        md = metre.DurationIndexer(score).run()
        durations = md['metre.DurationIndexer', part[1]]

        comb = pandas.concat([notes1, durations], axis=1)

        condition = comb[part] != 'Rest'
        location = comb['metre.DurationIndexer', part[1]]
        durations = location[condition].dropna().tolist()

        while 'Rest' in intervals:
            intervals.remove('Rest')

        all_iois.append(ioi_contour(durations))
        all_intvls.append(directed_mod12(intervals))

    return(all_iois, all_intvls)
