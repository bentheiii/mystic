from mysticweb.app import app
import mysticweb.routes
from mysticweb.__data import __version__, __author__
try:
    from mysticweb.secrets import __secret_key__
except ImportError:
    pass
else:
    app.secret_key = __secret_key__
    del __secret_key__
