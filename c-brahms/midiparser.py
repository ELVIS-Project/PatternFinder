from vis.analyzers.indexers import noterest, metre
import music21


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
        data.append(((onsets[x], notes[x]), (offsets[x], notes[x])))

    return data


def run(piece):
    """Given a file name, finds the notes with onsets and offsets for each part."""

    score = music21.converter.parse(piece)
    notes = noterest.NoteRestIndexer(score).run()
    md = metre.DurationIndexer(score).run()

    all_data = []
    for p in notes['noterest.NoteRestIndexer']:
        part = notes['noterest.NoteRestIndexer', p]
        durations = md['metre.DurationIndexer', p]
        data = parse_part(part, durations)
        all_data.extend(data)

    return all_data
