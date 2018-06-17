import sys
sys.path.insert(0, '/home/dgarfinkle/PatternFinder')

import os
import json
import multiprocessing

import music21
import yaml

from flask import Flask, request, redirect, url_for, render_template, send_from_directory, Response
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename

from app.dpw2 import algorithm
from patternfinder.geometric_helsinki import Finder

us = music21.environment.UserSettings()
us['directoryScratch'] = '/home/dgarfinkle/PatternFinder/music_files/music21_temp_output'

app = Flask(__name__)
Bootstrap(app)

app.config.update(TEMPLATES_AUTO_RELOAD=True)

QUERY_PATH = 'app/queries/'
RESULTS_PATH = 'app/results/'
PALESTRINA_PATH = 'music_files/corpus/Palestrina/'

DEFAULT_KRN_QUERY = """**kern
*clefG2
*k[]
*M4/4
=-
4c 4e 4a 4cc
4B- f b- dd
"""

def find(query, lock=multiprocessing.Lock()):
    progress_file = "{}{}.yml".format(RESULTS_PATH, query)

    lock.acquire()
    with open(progress_file, 'w') as f:
        yaml.dump({'progress': 0, 'occurrences': []}, f)
    lock.release()

    settings = {
            'scale': 'warped',
            'threshold': 0.85,
            'source_window': 10}

    masses = [m for m in os.listdir(PALESTRINA_PATH) if m[-3:] == 'xml']
    index = 0
    for mass in masses:
        print("Looking for query {} in mass {}".format(query, mass))

        for occ in Finder(QUERY_PATH + query + '.xml', PALESTRINA_PATH + mass, **settings):
            occ.ui_id = "{}_{}".format(query, index)
            for write_mthd, fmt in (('xml', '.xml'),):
                temp_file = occ.get_excerpt(color='red').write(write_mthd)
                os.rename(str(temp_file), "{}{}_{}{}".format(RESULTS_PATH, query, index, fmt))

            details = {
                'index': index,
                'max_window': occ.max_window,
                'length': len(occ.source_notes),
                'score': mass
            }
            print("Writing occ {} with details {}".format(index, details))

            lock.acquire()
            with open(progress_file, 'r') as f:
                progress = yaml.safe_load(f)
            progress['occurrences'].append(details)
            progress['progress'] = float(index) / len(masses)
            with open(progress_file, 'w') as f:
                yaml.dump(progress, f)
            lock.release()

            index += 1
"""
def find(query_id):

    _, _, masses = next(os.walk(PALESTRINA_PATH))
    for mass in [m for m in masses if m[-3:] == 'xml']:
        print("Looking for query {} in mass {}".format(query_id, mass))
        matrix = algorithm(music21.converter.parse(QUERY_PATH + query_id), music21.converter.parse(PALESTRINA_PATH + mass))
        with open(RESULTS_PATH + '{}-{}'.format(query_id, mass), 'w') as f:
            json.dump(matrix, f)
"""

@app.route('/vue/excerpt/<mass>/<note_indices>')
def vue_excerpt(mass, note_indices):
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

@app.route('/vue/search', methods=['GET'])
def vue_search():
    from app.dpwc import search_palestrina
    from patternfinder.geometric_helsinki.indexer import csv_notes, intra_vectors

    query = request.args['krnText']
    input_type = request.args['inputType']
    tmp_query_path = '.'.join(['app/queries/query', input_type])
    print("Received query: \n{}".format(query))
    with open(tmp_query_path, 'w') as f:
        f.write(query)

    intra_vectors(tmp_query_path)
    print("Query written to {} and indexed with suffix .notes".format(tmp_query_path))
    response = search_palestrina(tmp_query_path + '.vectors')
    print("serving krn " + query or DEFAULT_KRN_QUERY)
    return render_template('vue.html', response = response, default_krn = query or DEFAULT_KRN_QUERY)

@app.route('/vue')
def vueapp():
    return render_template('vue.html', response = [], default_krn = DEFAULT_KRN_QUERY)

@app.route('/')
def index():
    queries = []
    for q in os.listdir(QUERY_PATH):
        q_id = q[:-4]
        queries.append((q_id, url_for('view_queries', query_id=q_id, _external=True)))

    print(queries)
    return render_template('index.html', queries=queries, results_url=url_for('results_root', _external=True))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == "POST":
        queries = sorted([int(p.split('.')[0]) for p in os.listdir(QUERY_PATH)])
        # Take the lowest untaken number
        new_index = list(set(range(len(queries) + 1)) - set(queries))[0]

        file = request.files['file']
        file.save(QUERY_PATH + str(new_index) + '.xml')
        return redirect(url_for('search', query_id=new_index))

@app.route('/search/<query_id>', methods=['GET'])
def search(query_id):
    lock = multiprocessing.Lock()
    subps = multiprocessing.Process(target=find, args=[query_id, lock])
    subps.start()

    return redirect(url_for('index'))

@app.route('/results')
def results_root():
    return redirect(url_for('results', query_id='1'))

@app.route('/results/<path:query_id>/<path:result_id>', methods=['GET'])
def view_result(query_id, result_id):
    filename = "{}_{}.xml".format(query_id, result_id)
    return send_from_directory("results", filename)

@app.route('/queries/<query_id>')
def view_queries(query_id):
    filename = "{}.xml".format(query_id)
    return send_from_directory("queries", filename)

@app.route('/results/<query_id>', methods=['GET'])
def results(query_id):
    with open(RESULTS_PATH + query_id + '.yml', 'r') as f:
        results = yaml.safe_load(f)

    occs = [o for o in results['occurrences'] if (
        o['length'] >= int(request.args.get('threshold')) and
        o['max_window'] <= int(request.args.get('max_window')))]

    results = [o['index'] for o in occs]
    scores = [o['score'] for o in occs]

    urls = [url_for("view_result", query_id=query_id, result_id=result_id, _external=True)
            for result_id in results]
    # fetch from database
    #paths = [p.split('_') for p in os.listdir(RESULTS_PATH)]
    #results = [result.split('.')[0] for query, result in paths if query == str(query_id) and result[-3:] == 'xml']
    #urls = [url_for("result", query_id=query_id, result_id=result, _external=True) for result in results]
    data = [(query_id, result_id, score, url) for result_id, score, url in zip(results, scores, urls)]
    return render_template("results.html", data=data, total_num = len(results))
