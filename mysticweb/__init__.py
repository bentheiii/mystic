from mysticweb.app import app
import mysticweb.routes

from mysticweb.secrets import __secret_key__

app.secret_key = __secret_key__

del __secret_key__
