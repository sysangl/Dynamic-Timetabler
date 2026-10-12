from flask import Flask, request, jsonify
import uuid
from routes import (
    settings as settings_route,
    users as users_route,
    app as app_route,
    activities as activities_route
)
from models import (
    db,
)

def initialise_routes(app: Flask):
    app_route.create_routes(app)
    users_route.create_routes(app)
    settings_route.create_routes(app)
    activities_route.create_routes(app)

