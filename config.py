import toml,os,sys
from pathlib import Path
import threading, shutil
from pathlib import Path

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

_DEFAULT_CFG = Path(resource_path('config')) / 'default.toml'
_USER_CFG = Path.home() / '.dynamic-timetabler' / 'default.toml'

_lock = threading.RLock()

def _read_config(path: Path) -> dict:
    with path.open("r") as f:
        return toml.load(f)


def _deep_merge(a: dict, b: dict) -> dict:
    r = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(r.get(k), dict):
            r[k] = _deep_merge(r[k], v)
        else:
            r[k] = v
    return r

def _load_config():
    if not _USER_CFG.exists():
        _USER_CFG.mkdir(parents=True, exist_ok=True)
        shutil.copy(src=_DEFAULT_CFG, dst=_USER_CFG)

    default_cfg = _read_config(_DEFAULT_CFG)
    user_cfg = _read_config(_USER_CFG)
    return _deep_merge(default_cfg, user_cfg)

CONFIG = _load_config()

def get_config():
    return CONFIG

def reload_config():
    global CONFIG
    with _lock:
        CONFIG = _load_config()