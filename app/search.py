import sys
sys.path.insert(0, '/home/dgarfinkle/PatternFinder')

import os
import json
import multiprocessing

import music21

from flask import Flask, request, redirect, url_for, render_template, send_from_directory
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename

from app.dpw2 import algorithm
from patternfinder.geometric_helsinki import Finder

us = music21.environment.UserSettings()
us['directoryScratch'] = '/home/dgarfinkle/PatternFinder/music_files/music21_temp_output'

app = Flask(__name__)
Bootstrap(app)

QUERY_PATH = 'app/queries/'
RESULTS_PATH = 'app/results/'
PALESTRINA_PATH = 'music_files/corpus/Palestrina/'

def find(query):
    index = 0
    settings = {
            'scale': 'warped',
            'threshold': 'all',
            'source_window': 9}
    _, _, masses = next(os.walk('music_files/corpus/Palestrina'))
    for mass in (m for m in masses if m[-3:] == 'xml'):
        print("Looking for query {} in mass {}".format(query, mass))
        for occ in Finder(QUERY_PATH + query + '.xml', PALESTRINA_PATH + mass, **settings):
            occ.ui_id = "{}_{}".format(query, index)
            for write_mthd, fmt in (('lily.pdf', '.pdf'), ('xml', '.xml')):
                temp_file = occ.get_excerpt(color='red').write(write_mthd)
                os.rename(str(temp_file), "{}{}_{}{}".format(RESULTS_PATH, query, index, fmt))
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
@app.route('/')
def index():
    return render_template('index.html', url=url_for('results', result_id='1_1..xml', _external=True))

@app.route('/search', methods=['GET', 'POST'])
def upload():
    if request.method == "POST":
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['queries'], filename))
        return redirect(url_for('search', query_id=filename))

    elif request.method == "GET":
        return render_template('upload.html')

@app.route('/search/<query_id>', methods=['GET'])
def search(query_id):
    subps = multiprocessing.Process(target=find, args=[query_id])
    subps.start()

    return render_template('upload.html')

@app.route('/results/<path:query_id>/<path:result_id>', methods=['GET'])
def result(query_id, result_id):
    filename = "{}_{}.xml".format(query_id, result_id)
    return send_from_directory("results", filename)

@app.route('/queries/<query_id>')
def view_queries(query_id):
    filename = "{}.xml".format(query_id)
    return send_from_directory("queries", filename)

@app.route('/results/<query_id>', methods=['GET'])
def results(query_id):
    # fetch from database
    paths = [p.split('_') for p in os.listdir("results")]
    print(paths)
    results = [result.split('.')[0] for query, result in paths if query == str(query_id) and result[-3:] == 'xml']
    print(results)
    urls = [url_for("result", query_id=query_id, result_id=result, _external=True) for result in results]
    print(urls)
    data = [(query_id, result_id, url) for result_id, url in zip(results, urls)]
    return render_template("results.html", data=data, query_url=url_for("view_queries", query_id=query_id))
