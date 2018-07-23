from flask import render_template, request

from mysticweb.app import app
from mysticweb.__util import *

from mysticlib import Mystic

@app.route('/', methods=['POST', 'GET'])
def get_file():
    if request.method == 'POST':
        if request.form.get('source_kind') == 'url':  # todo remember
            success, raw_source = download_page(request.form.get('url'))
            if not success:
                return render_template('error.html', error_string=str(raw_source))
        elif request.form.get('source_kind') == 'file':
            file = request.files.get('file')
            try:
                raw_source = file.read()
            except Exception as e:
                return render_template('error.html', error_string=str(e))
        else:
            return render_template('error.html', error_string='the source kind must be valid')
        return repr(raw_source)
    return render_template('input.html')
