from __future__ import print_function
import music21
import re
import os
import pdb
import patternfinder.geometric_helsinki

GJERD_DIR = "evaluation/gjerdingen"
TAVERN_DIR = "music_files/TAVERN"

MOZART_PICKLE_PATH = os.path.join(GJERD_DIR, "tavern_mozart_scores.pckl")
SCHEMATA_PATH = os.path.join(GJERD_DIR, "schemata.xml")

# COLLECT MOZART THEMES AND VARIATIONS
def collect_streams(input_dir):
    """collect_streams() returns a list of (file_name, file_parsed_stream) tuples"""
    scores = []
    for root, dirs, files in os.walk(os.path.join(input_dir)):
        for maybe_kern in files:
            if re.match("[BM].*_score\.krn", maybe_kern):
                file_path = os.path.join(root, maybe_kern)
                print("parsing " + file_path)
                try:
                    score_stream = music21.converter.parse(file_path)
                except:
                    continue
                score_stream.occurrences = 0
                score_stream.filename = maybe_kern
                scores.append(score_stream)
    return scores

def add_local_corpus():
    tavern_corpus = music21.corpus.corpora.LocalCorpus()
    tavern_corpus.addPath('evaluation/gjerdingen/tavern')
    tavern_corpus.cacheMetadata()

def get_sources():
    return [(os.path.basename(f), music21.converter.parse(f)) for f in music21.corpus.manager.fromName('local').getPaths()]

def isolate_outer_voices(p):
    # Lower voice
    for note_object in p.parts[1].flat.notes:
        if note_object.isChord:
            note_object.sortAscending()
            for pitch in note_object.pitches[1:]:
                note_object.remove(pitch)
    # Upper voice
    for note_object in p.parts[0].flat.notes:
        if note_object.isChord:
            note_object.sortAscending()
            for pitch in note_object.pitches[:-1]:
                note_object.remove(pitch)

def multi_search(pattern, sources, settings, output_dir):
    for source in sources:
        print(' '.join(['\nSearching in ', source.filename, ' ']), end='')
        for pattern in patterns:
            # Look for the pattern in the source
            print(pattern.metadata.title, end='.. ')
            for occ in patternfinder.geometric_helsinki.Finder(pattern, source, **settings):
                print('|', end='')
                # Color the notes in the source
                for note in occ.notes:
                    note.style.color = pattern.style.color
        if any(note.style.color for note in source.flat.notes):
            source.write('xml', os.path.join(
                # Folder
                output_dir,
                # File
                "pf_{0}.xml".format(source.filename)))

### GET QUERIES
schemata = music21.converter.parse(SCHEMATA_PATH)
schemata_excerpts = (
        ('fonte', 'red', schemata.measures(1,2)),
        ('quiescenza', 'blue', schemata.measures(3, 6)),
        ('prinner', 'orange', schemata.measures(7, 10)))
patterns = []
for name, color, stream_excerpt in schemata_excerpts:
    stream_excerpt.metadata = music21.metadata.Metadata()
    stream_excerpt.metadata.title = name
    stream_excerpt.style.color = color
    patterns.append(stream_excerpt)

# Delete middle voices of queries
for p in patterns:
    isolate_outer_voices(p)


### GET SOURCES
#sources = collect_streams(TAVERN_DIR)

output_dir = os.path.join(GJERD_DIR, 'data')
settings = {
        'scale' : 'warped',
        'threshold' : 0.80,
        'source_window' : 10,
        'pattern_window' : 3}
multi_search(patterns, sources, settings, output_dir)

