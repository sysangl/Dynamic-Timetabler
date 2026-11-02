# app/routes/__init__.py
import logging

from flask import Flask, jsonify, render_template, request

from .app import bp as app_bp
from .auth import bp as auth_bp
from .engine import bp as engine_bp
from .schedule import bp as schedules_bp
from .settings import bp as settings_bp
from .timetable import bp as timetable_bp
from .users import bp as users_bp

BLUEPRINTS = (
    (auth_bp, "/auth"),
    (app_bp,"/app"),
    (settings_bp,"/api/users/settings"),
    (timetable_bp,"/api/timetable"),
    (users_bp,"/api/users"),
    (engine_bp,"/api/engine"),
    (schedules_bp, "/api/schedules")
)

def _register_blueprints(app: Flask)->None:
    for blueprint, prefix in BLUEPRINTS:
        app.register_blueprint(blueprint, url_prefix=prefix)

def _register_utility_routes(app: Flask)->None:
    @app.route("/health")
    def health():
        """health-check ep"""
        return jsonify({"status":"ok"})

    @app.errorhandler(404)
    def not_found(e):
        page = request.url.split('/')[-1]
        if len(page) >= 15:
            page = page[:10]+'...'
        return render_template('404.html', url_string=page), 404


def register_routes(app: Flask) -> None:
    log = logging.getLogger("app")
    log.info("Initialising routes")

    log.info("Registering blueprints")
    _register_blueprints(app)

    log.info("Registering utility routes")
    _register_utility_routes(app)

