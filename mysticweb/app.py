import flask

app = flask.Flask('mysticweb')
app.config['MAX_CONTENT_PATH'] = 1_000*1_000*1 # 1 meg