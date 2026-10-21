import toml,logging
from pathlib import Path
import threading, shutil
from pathlib import Path
from helpers.paths import resource_path

server_logger = logging.getLogger("server")
PROJECT_NAME = 'canopy-suite'
_DEFAULT_CFG = Path(resource_path('config')) / 'default.toml'
_USER_CFG = Path.home() / f'.{PROJECT_NAME}' / 'default.toml'

_lock = threading.RLock()
def _read_config(path: Path) -> dict:
    try:
        with path.open("r") as f:
            return toml.load(f)
    except Exception:
        server_logger.exception("Failed to read config")
        raise

def _deep_merge(a: dict, b: dict) -> dict:
    r = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(r.get(k), dict):
            r[k] = _deep_merge(r[k], v)
        else:
            r[k] = v
    return r

def _load_config():
    server_logger.info("Loading config...")
    if not _USER_CFG.exists():
        server_logger.info(f"Copying default config to ~/.{PROJECT_NAME}/")
        _USER_CFG.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src=_DEFAULT_CFG, dst=_USER_CFG)

    default_cfg = _read_config(_DEFAULT_CFG)
    user_cfg = _read_config(_USER_CFG)
    return _deep_merge(default_cfg, user_cfg)

CONFIG = _load_config()

def get_config(default=False):
    if default:
        return _read_config(_DEFAULT_CFG)
    return CONFIG

def reload_config():
    global CONFIG
    with _lock:
        CONFIG = _load_config()

def write_config(config:dict):
    _USER_CFG.parent.mkdir(parents=True, exist_ok=True)
    with _USER_CFG.open("w",encoding="utf-8") as f:
        toml.dump(config, f)
    server_logger.info("Configuration created/updated")