from flask import Flask, request, jsonify
import uuid
from src.models import (
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
from src.routes import (
    app as app_route,
    users as users_route,
    settings as settings_route,
)

def initialise_routes(app: Flask):
    app_route.create_routes(app)
    users_route.create_routes(app)
    settings_route.create_routes(app)

