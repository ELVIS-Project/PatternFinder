import sys
sys.path.insert(0, '../')

import os
import json
import multiprocessing

import music21
import yaml

from flask import Flask, request, redirect, url_for, render_template, send_from_directory, Response, send_file
from flask_bootstrap import Bootstrap
from flask_cors import CORS
from werkzeug.utils import secure_filename

from app.dpwc import search_palestrina
from patternfinder.geometric_helsinki.indexer import csv_notes, intra_vectors

us = music21.environment.UserSettings()
us['directoryScratch'] = '/app/patternfinder/music_files/music21_temp_output'

app = Flask(__name__)
Bootstrap(app)
CORS(app)

app.config.update(TEMPLATES_AUTO_RELOAD=True)

QUERY_PATH = 'app/queries/'
RESULTS_PATH = 'app/results/'
PALESTRINA_PATH = '/app/patternfinder/music_files/corpus/Palestrina/'

DEFAULT_KRN_QUERY = """**kern
*clefG2
*k[]
*M4/4
=-
4c 4e 4a 4cc
4B- f b- dd
"""

@app.route('/xml/<mass>')
def xml(mass):
    path = PALESTRINA_PATH + mass + '.mid.xml'
    with open(path, 'r') as f:
        xml = f.read()
    return Response(xml, mimetype='application/xml')

@app.route('/mass/<mass>')
def mass(mass):
    return render_template("vue_mass.html", mass=mass)

@app.route('/mass/<mass>/excerpt/<note_indices>')
def excerpt(mass, note_indices):
    from patternfinder.geometric_helsinki.geometric_notes import NotePointSet
    score = music21.converter.parse(PALESTRINA_PATH + mass + '.mid.xml')
    pointset = list(NotePointSet(score).flat.notes)

    pointset_indices = [int(i) for i in note_indices.split(',')]
    score_note_ids = [pointset[i].original_note_id for i in pointset_indices]

    # Get stream excerpt
    _, start_measure = score.beatAndMeasureFromOffset(pointset[pointset_indices[0]].offset)
    _, end_measure = score.beatAndMeasureFromOffset(pointset[pointset_indices[-1]].offset + pointset[-1].duration.quarterLength - 1)
    excerpt = score.measures(numberStart=start_measure.number, numberEnd=end_measure.number)

    # Colour notes
    for note in excerpt.flat.notes:
        if note.id in score_note_ids:
            note.style.color = 'red'

    # Delete part names (midi files have bad data)
    for part in excerpt:
        part.partName = ''

    sx = music21.musicxml.m21ToXml.ScoreExporter(excerpt)
    musicxml = sx.parse()

    from io import StringIO
    import sys
    bfr = StringIO()
    sys.stdout = bfr
    sx.dump(musicxml)
    output = bfr.getvalue()
    sys.stdout = sys.__stdout__
    return Response(output, mimetype='application/xml')

@app.route('/search', methods=['GET'])
def search():
    query_str = request.args['krnText']
    input_type = request.args['inputType']

    print("Received query: \n{}".format(query_str))
    indexed_query = intra_vectors(query_str, dest="str", window=1)
    print("Query indexed.")

    response = search_palestrina(indexed_query, PALESTRINA_PATH)
    print("serving krn " + query_str or DEFAULT_KRN_QUERY)
    return render_template('index.html', response = response, default_krn = query_str or DEFAULT_KRN_QUERY)

@app.route('/')
def index():
    #return render_template('vue.html', response = [], default_krn = DEFAULT_KRN_QUERY)
    return render_template('index.html', response = [], default_krn = DEFAULT_KRN_QUERY)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
