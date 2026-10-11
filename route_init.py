from flask import Flask, request, jsonify
import uuid
from routes import settings as settings_route, users as users_route
from models import (
    db,
    ToDo,
    Task,
    Block,
    ClassBlock,
    Activity,
    Subject,
    User,
    Settings
)
from routes import (
    app as app_route,
)

def initialise_routes(app: Flask):
    app_route.create_routes(app)
    users_route.create_routes(app)
    settings_route.create_routes(app)

