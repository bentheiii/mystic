from io import BytesIO

from flask import render_template, request, redirect, send_from_directory, after_this_request, g

from mysticlib import Mystic, BadKey

from mysticweb.app import app
from mysticweb.exceptions import DumpError
from mysticweb.__util import *
from mysticweb.__data import *

git_path = "http://github.com/bentheiii/mystic"


def add_warning(warning):
    try:
        g.warnings.append(warning)
    except AttributeError:
        g.warnings = [warning]


@app.before_request
def startup():
    g.__version__ = __version__
    g.__author__ = __author__
    if not request.is_secure and not is_local(request.url):
        add_warning("This connection is non-local and not secure!"
                    " Do not enter your password or mystic here unless you know what you're doing!")


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder,
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.errorhandler(DumpError)
def error(e):
    while e.__cause__:
        e = e.__cause__
    return render_template('error.html', error_string=f'{type(e).__name__}: {e.args[0]}'), 400


def process_input(raw_source, password, pre_load_filter, check_weak=True):
    stream = BytesIO(raw_source)
    try:
        mystic = Mystic.from_stream(stream)
    except (ValueError, EOFError) as e:
        raise DumpError from e
    mystic.password_callback = lambda x: password
    try:
        try:
            mystic.mutable = True
        except Exception:
            pass

        if pre_load_filter:
            d = ((k, str(v)) for (k, v) in mystic.items() if
                 fuzzy_in(pre_load_filter, k))
        else:
            d = ((k, str(v)) for (k, v) in mystic.items())
        d = list(d)
    except BadKey:
        raise DumpError('a bad password was entered')

    if check_weak:
        p_str = pass_strength(password)

        if p_str is not None:
            add_warning(f'your password has been rated as {p_str}, consider changing it!')

    return render_template('dump.html', results=d)


@app.route('/', methods=['POST', 'GET'])
def main():
    c_url = request.cookies.get('url_rem', '')

    if request.method == 'POST':
        if request.form.get('source_kind') == 'url':
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
                raise DumpError from raw_source
        elif request.form.get('source_kind') == 'file':
            file = request.files.get('file')
            try:
                raw_source = file.read()
            except Exception as e:
                raise DumpError from e
        else:
            raise DumpError('the source kind must be valid')
        password = request.form.get('password')
        pre_load_filter = request.form.get('pre_load_filter')
        return process_input(raw_source, password, pre_load_filter)

    return render_template('input.html', url=c_url)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/src')
@app.route('/src/<path:path>')
def src(path=''):
    return redirect(git_path + path)
