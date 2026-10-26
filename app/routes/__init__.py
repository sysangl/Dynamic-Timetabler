# app/routes/__init__.py
import logging

from flask import Flask, jsonify

from .app import bp as app_bp
from .auth import bp as auth_bp
from .settings import bp as settings_bp
from .settings import create_routes as settings_create_routes
from .timetable import bp as timetable_bp
from .timetable import create_routes as timetable_create_routes
from .users import bp as users_bp
from .users import create_routes as user_create_routes


def initialise_routes(app: Flask) -> None:
    logger = logging.getLogger("server")
    logger.info("Initialising routes")

    timetable_create_routes(app)
    settings_create_routes(app)
    user_create_routes(app)

    app.register_blueprint(auth_bp, url_prefix="/auth")

    app.register_blueprint(app_bp,url_prefix="/app")
    app.register_blueprint(settings_bp,url_prefix="/api/users/settings")
    app.register_blueprint(timetable_bp,url_prefix="/api/timetable")
    app.register_blueprint(users_bp,url_prefix="/api/users")

    @app.route("/health")
    def health():
        """health-check ep"""
        return jsonify({"status":"ok"})

    # @app.errorhandler(404)
    # def page_not_found(e):
    #     return 404 template