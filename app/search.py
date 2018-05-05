import sys
sys.path.insert(0, '/home/dgarfinkle/PatternFinder')
import os

from flask import Flask, request, redirect, url_for
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
from patternfinder.geometric_helsinki import Finder

app = Flask(__name__)
Bootstrap(app)

"""
def find(query):
    _, _, masses = next(os.walk('music_files/corpus/Palestrina'))
    for mass in masses:
        for index, occ in enumerate(Finder(query, mass)):
            temp_file = occ.get_excerpt(color='red', left_padding=1, right_padding=1).write('lily.pdf')
            os.rename(temp_file, "results/mass_{}".format(d))
"""
@app.route('/')
def hello_world():
    return "hello world"

@app.route('/search', methods=['GET', 'POST'])
def upload():
    #if request.method == "POST":
        #filename = secure_filename(file.filename)
        #file.save(os.path.join(app.config['queries'], filename))
        #find(file)
        #return redirect(url_for('search', filename=filename))
    return render_template('upload.html')

"""
@app.route('/search/<filename>', methods=['GET'])
def search(filename):
    return render_template('results.html')
"""

