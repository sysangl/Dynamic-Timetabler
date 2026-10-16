from app import create_app
from helpers.config import get_config, reload_config
from route_init import initialise_routes
from helpers.logging_conf import initialise_logging
import multiprocessing,os,sys
import logging, atexit

initialise_logging()
multiprocessing.freeze_support()

config = get_config()
app = create_app()
initialise_routes(app)
server_logger = logging.getLogger('server')
app.run(debug=config['server']['debug'], host=config['server']['host'], port=config['server']['port'])

def server_stop():
    server_logger.info("Shutting down server")

atexit.register(server_stop)