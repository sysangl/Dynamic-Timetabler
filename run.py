from app import create_app
from config import get_config, reload_config
from route_init import initialise_routes
import multiprocessing,os,sys

multiprocessing.freeze_support()

def resource_path(relative_path):
    """
    Return the absolute path to a resource, whether the app is
    running from a PyInstaller bundle or from source.
    """
    if getattr(sys, 'frozen', False):          # PyInstaller bundle
        base_path = sys._MEIPASS             # type: ignore # temporary extraction folder
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)



config = get_config()
app = create_app()
initialise_routes(app)
app.run(debug=config['server']['debug'], host=config['server']['host'], port=config['server']['port'])