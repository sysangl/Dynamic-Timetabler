import logging
import logging.config

from helpers.config import _get_data_dir

_LOG_PATH = _get_data_dir() / "logs"
_LOG_FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def _rotating_handler(name: str) -> dict:
    return {
        "class" : "logging.handlers.RotatingFileHandler",
        "level" : "DEBUG",
        "formatter" : "standard",
        "filename" : str(_LOG_PATH / f"{name}.log"),
        "mode" : "a",
        "maxBytes": 2000000, # 2 MiB
        "backupCount" : 5,
        "encoding" : "utf-8"
    }


def initialise_logging():
    _LOG_PATH.mkdir(parents=True, exist_ok=True)
    print("Activating Loggers")
    
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers' : False,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            },
            'standard' : {
                'format': _LOG_FMT,
                'datefmt': _DATE_FMT
            }
        },
        'handlers': {
            'wsgi': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default'
            },
            'server_file' : _rotating_handler('server'),
            'database_file': _rotating_handler('database'),
            'app_file': _rotating_handler('app'),
        },
        'loggers': {
            'server': {
                'level': "DEBUG",
                'handlers':['server_file'],
                'propagate': False,
            },
            'database': {
                'level': "DEBUG",
                'handlers':['database_file'],
                'propagate': False,
            },
            'app': {
                'level': "DEBUG",
                'handlers':['app_file'],
                'propagate': False,
            },
        },
        'root': {
            'level': 'INFO',
            'handlers': ['wsgi']
        }
    })

