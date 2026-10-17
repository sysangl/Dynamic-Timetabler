from app import create_app
from helpers.config import get_config, reload_config
from helpers.logging_conf import initialise_logging
import multiprocessing,os,sys
import logging, atexit

initialise_logging()
multiprocessing.freeze_support()

config = get_config()
app = create_app()


print( "==========================================================================")
print(r"        ___                             _                                 ")     
print(r"       /   \_   _ _ __   __ _ _ __ ___ (_) ___                            ")
print(r"      / /\ / | | | '_ \ / _` | '_ ` _ \| |/ __|                           ")
print(r"     / /_//| |_| | | | | (_| | | | | | | | (__                            ")
print(r"    /___,'  \__, |_| |_|\__,_|_| |_| |_|_|\___|                           ")
print(r"            |___/                                                         ")
print(r"                    _____ _                _        _     _               ")
print(r"                   /__   (_)_ __ ___   ___| |_ __ _| |__ | | ___ _ __     ")
print(r"                     / /\/ | '_ ` _ \ / _ \ __/ _` | '_ \| |/ _ \ '__|    ")
print(r"                    / /  | | | | | | |  __/ || (_| | |_) | |  __/ |       ")
print(r"                    \/   |_|_| |_| |_|\___|\__\__,_|_.__/|_|\___|_|       ")
print(r"                                                                          ")
print(r"        ( SERVER & WEB INTERFACE )                                        ")
print(r"                                                                          ")
print( "==========================================================================")
print()
print( "================================== INFO ==================================")
print(f" To open the web interface go to 'http://{config['server']['host']}:{config['server']['port']}/app ")
print( "==========================================================================")
if config['server']['debug']:
    print()
    print("================================= URL MAP =================================")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint:35s} {rule}")
    print("===========================================================================\n")
server_logger = logging.getLogger('server')
app.run(debug=config['server']['debug'], host=config['server']['host'], port=config['server']['port'])


def server_stop():
    server_logger.info("Shutting down server")

atexit.register(server_stop)