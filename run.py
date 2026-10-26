def run_server():
    from app import create_app
    from helpers.config import get_config, reload_config
    from helpers.logging_conf import initialise_logging
    import multiprocessing
    import logging, atexit

    initialise_logging()
    multiprocessing.freeze_support()

    config = get_config()
    app = create_app()

    print( "==========================================================================")
    print(r"               _____                                                      ")
    print(r"              /  __ \                                                     ")
    print(r"              | /  \/ __ _ _ __   ___  _ __  _   _                        ")
    print(r"              | |    / _` | '_ \ / _ \| '_ \| | | |                       ")
    print(r"              | \__/\ (_| | | | | (_) | |_) | |_| |                       ")
    print(r"               \____/\__,_|_| |_|\___/| .__/ \__, |                       ")
    print(r"                                      | |     __/ |                       ")
    print(r"                                      |_|    |___/                        ")
    print(r"                                                                          ")
    print(r"        Productivity Suite                                                ")
    print(r"                                         Server View                      ")
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

if __name__ == "__main__":
    run_server()