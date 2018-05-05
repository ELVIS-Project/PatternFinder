import os
import music21

def color_occurrence_in_stream(occ, stream):
    flattened_stream = stream.flat
    for source_note in occ.source_notes

def write_stream_with_dict_prefix(*args, stream, filepath, dct, filename):
    output = stream.write(*args)
    os.rename(output, os.path.join(filepath, "_".join(dct.values()), filename))


