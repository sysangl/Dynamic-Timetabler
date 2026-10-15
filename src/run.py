from app import create_app
from config import Config
from route_init import initialise_routes
import multiprocessing

multiprocessing.freeze_support()

Config.load_config("config/testing.toml")
config = Config.config
app = create_app()
initialise_routes(app)
app.run(debug=config['server']['debug'], host=config['server']['host'], port=config['server']['port'])