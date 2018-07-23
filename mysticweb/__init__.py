from mysticweb.app import app
import mysticweb.routes

try:
    from mysticweb.secrets import __secret_key__
except ImportError:
    pass
else:
    app.secret_key = __secret_key__
    del __secret_key__
# todo icon
