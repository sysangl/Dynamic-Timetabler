import sys, os, logging
from pathlib import Path

server_logger = logging.getLogger('server')

def resource_path(relative_path):
    """
    Return the absolute path to a resource, whether the app is
    running from a PyInstaller bundle or from source.
    """
    server_logger.info(f'Resolving {relative_path}')
    if getattr(sys, 'frozen', False):          # PyInstaller bundle
        base_path = sys._MEIPASS             # type: ignore # temporary extraction folder
    else:
        base_path = Path(__file__).resolve().parent.parent # since this is in helpers folder, we need to return it's parent folder
    server_logger.info(os.path.join(base_path, relative_path))
    return os.path.join(base_path, relative_path)