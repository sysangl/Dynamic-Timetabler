from app import create_app
from helpers.config import get_config, reload_config
from helpers.logging_conf import initialise_logging
import multiprocessing,os,sys
import logging, atexit

initialise_logging()
multiprocessing.freeze_support()

config = get_config()
app = create_app()
print("\n=== URL MAP ===")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint:30s} {rule}")
print("================\n")
server_logger = logging.getLogger('server')
app.run(debug=config['server']['debug'], host=config['server']['host'], port=config['server']['port'])

def server_stop():
    server_logger.info("Shutting down server")

atexit.register(server_stop)