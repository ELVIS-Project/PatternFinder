from vis.analyzers.indexers import noterest, metre
from LineSegment import LineSegment
import music21
import pdb

def to_midi(name):
    """Translate note names into midi pitches."""

    if name == 'Rest':
        return name
    else:
        c = music21.pitch.Pitch(name)
        return c.midi


def parse_part(part, meters):
    """Parses each part and finds the onsets, offsets and pitches of each note."""
    part = part.dropna().map(to_midi)
    meters = meters.dropna()

    notes = part.values.tolist()
    if 'Rest' in notes:
        while 'Rest' in notes:
            notes.remove('Rest')
        condition = part != 'Rest'
        meters = meters[condition]
    lengths = meters.values.tolist()
    onsets = meters.index.tolist()

    startlen = zip(*[onsets, lengths])
    offsets = [(pair[0] + pair[1]) for pair in startlen]

    data = []
    for x in range(len(notes)):
#        data.append(((onsets[x], notes[x]), (offsets[x], notes[x])))
#        data.append([onsets[x], notes[x]])
        data.append([onsets[x], lengths[x], notes[x]])

    return [LineSegment(d) for d in data]

def get_measure_and_beat_from_onset(onset, indexed_piece):
    measure_number = indexed_piece[('metre.MeasureIndexer', '0')].loc[onset]
    start_of_measure = min(indexed_piece[indexed_piece[('metre.MeasureIndexer', '0')] == measure_number].index.tolist())
    relative_onset = onset - start_of_measure

    return (measure_number, relative_onset)

def run(indexed_piece):
    """Given a file name, finds the notes with onsets and offsets for each part."""

    all_data = []
    for p in indexed_piece['noterest.NoteRestIndexer']:
        part = indexed_piece['noterest.NoteRestIndexer', p]
        durations = indexed_piece['metre.DurationIndexer', p]
        data = parse_part(part, durations)
        all_data.extend(data)

    return all_data
