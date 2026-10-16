from flask import Flask
import logging
from routes import (
    settings as settings_route,
    users as users_route,
    app as app_route,
    activities as activities_route,
    timetable as timetable_route
)
from models import (
    db,
)

def initialise_routes(app: Flask):
    logging.getLogger('server').info("Initialising Routes")
    app_route.create_routes(app)
    users_route.create_routes(app)
    settings_route.create_routes(app)
    activities_route.create_routes(app)
    timetable_route.create_routes(app)

