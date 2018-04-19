import os

from flask import Flask, request, redirect, url_for
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
#from .. import patternfinder
import verovio

app = Flask(__name__)
Bootstrap(app)


@app.route('/search', methods=['GET', 'POST'])
def upload():
    if request.method == "POST":
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['queries'], filename))
        return redirect(url_for('search', filename=filename))
    return render_template('upload.html')

@app.route('/search/<filename>', methods=['GET'])
def search(filename):
    tk = verovio.toolkit()
    tk.loadFile(os.path.join(app.config['queries'], filename))
    return tk.renderToSvgFile()
