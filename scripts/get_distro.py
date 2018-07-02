from vis.models.indexed_piece import Importer
from itertools import islice
from collections import Counter
import pickle
import os


def count_notes():
    def get_notes(row):
            return tuple(sorted(set([n[0] if n[1].isdigit() else n[0:2] for n in tuple((tuple(row))[1]) if n != 'Rest'])))

    prog_counter = Counter()
    i = 0

    for m in [p for p in os.listdir('music_files/corpus/Palestrina/') if p[-3:] == 'xml']:
        print("processing " + m)
        ip = Importer('music_files/corpus/Palestrina/' + m)
        df = ip.get_data('noterest').fillna(method="ffill")
        it = zip(df.iterrows(), islice(df.iterrows(), 1, None))
        for row in it:
            notes = tuple(map(get_notes, row))
            prog_counter.update((notes, ))

        if i % 100 == 0:
            with open('scripts/prog.pckl', 'wb') as f:
                pickle.dump(prog_counter, f)

    with open('scripts/prog.pckl', 'wb') as f:
        pickle.dump(prog_counter, f)

def count_intervals():
    def get_ints(row, num_voices):
        return tuple(sorted(set(n for n in tuple((tuple(row))[1]) if n != 'Rest'), key = lambda n: abs(int(n)))[:num_voices-1])
    prog_counter = Counter()
    i = 0

    vert_settings = {
        'quality': 'chromatic',
        'simple or compound': 'simple',
        'directed': True
    }

    for m in [p for p in os.listdir('music_files/corpus/Palestrina/') if p[-3:] == 'xml']:
        print("processing " + m)
        num_voices = m.split('_')[-1][0]
        if num_voices.isdigit():
            num_voices = int(num_voices)
        else:
            print("skipping " + m)
            continue
        ip = Importer('music_files/corpus/Palestrina/' + m)
        df = ip.get_data('vertical_interval', settings=vert_settings).fillna(method="ffill")

        note_df = ip.get_data('noterest').fillna(method="ffill")

        #int_df = df['interval.IntervalIndexer']

        it = zip(df.iterrows(), islice(df.iterrows(), 1, None))
        for row in it:
            ints = tuple(get_ints(r, num_voices) for r in row)
            prog_counter.update((ints, ))

        if i % 100 == 0:
            with open('scripts/prog.pckl', 'wb') as f:
                pickle.dump(prog_counter, f)

    with open('scripts/prog.pckl', 'wb') as f:
        pickle.dump(prog_counter, f)

    return prog_counter, df

if __name__ == "__main__":
    counter, df = count_intervals()

