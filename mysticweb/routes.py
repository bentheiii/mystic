from io import BytesIO

from flask import render_template, request, redirect, send_from_directory, after_this_request

from mysticlib import Mystic, BadKey

from mysticweb.app import app
from mysticweb.__util import *
from mysticweb.__data import __version__

git_path = "http://github.com/bentheiii/mystic"


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder,
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


def error(error_string):
    return render_template('error.html', error_string=error_string), 400


def process_input(raw_source, password, pre_load_filter):
    # todo weak password warnings
    stream = BytesIO(raw_source)
    try:
        mystic = Mystic.from_stream(stream)
    except (ValueError, EOFError) as e:
        return error(repr(e))
    mystic.password_callback = lambda x: password
    try:
        try:
            mystic.mutable = True
        except Exception:
            pass

        if pre_load_filter:
            d = ((k, str(v)) for (k, v) in mystic.items() if
                 fuzzy_in(pre_load_filter, k))  # todo smarter filtering (in js too)
        else:
            d = ((k, str(v)) for (k, v) in mystic.items())
        d = list(d)
    except BadKey:
        return error(repr('a bad password was entered'))
    return render_template('dump.html', results=d)


@app.route('/', methods=['POST', 'GET'])
def main():
    c_url = request.cookies.get('url_rem', '')

    if request.method == 'POST':
        if request.form.get('source_kind') == 'url':  # todo remember
            url = request.form.get('url')
            if request.form.get('url_remember'):
                rem_url = url
            else:
                rem_url = ''

            if rem_url != c_url:
                @after_this_request
                def set_url_rem(response):
                    response.set_cookie('url_rem', rem_url)
                    return response

            success, raw_source = download_page(url)
            if not success:
                return error(str(raw_source))
        elif request.form.get('source_kind') == 'file':
            file = request.files.get('file')
            try:
                raw_source = file.read()
            except Exception as e:
                return error(str(e))
        else:
            return error('the source kind must be valid')
        password = request.form.get('password')
        pre_load_filter = request.form.get('pre_load_filter')
        return process_input(raw_source, password, pre_load_filter)

    return render_template('input.html', url=c_url)


@app.route('/about')
def about():
    return render_template('about.html', version=__version__)


@app.route('/src')
@app.route('/src/<path:path>')
def src(path=''):
    return redirect(git_path + path)
