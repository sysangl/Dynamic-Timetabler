# app/routes/__init__.py
import logging
from flask import Flask, jsonify
from .auth import bp as auth_bp
from .activities import bp as activities_bp
from .app import bp as app_bp
from .settings import bp as settings_bp, create_routes as settings_create_routes
from .timetable import bp as timetable_bp, create_routes as timetable_create_routes
from .users import bp as users_bp, create_routes as user_create_routes
def initialise_routes(app: Flask) -> None:
    logger = logging.getLogger("server")
    logger.info("Initialising routes")

    timetable_create_routes(app)
    settings_create_routes(app)
    user_create_routes(app)

    app.register_blueprint(auth_bp, url_prefix=f"/auth")

    app.register_blueprint(activities_bp,url_prefix=f"/api/activities")
    app.register_blueprint(app_bp,url_prefix=f"/app")
    app.register_blueprint(settings_bp,url_prefix=f"/api/users/settings")
    app.register_blueprint(timetable_bp,url_prefix=f"/api/timetable")
    app.register_blueprint(users_bp,url_prefix=f"/api/users")

    @app.route("/health")
    def health():
        """health-check ep"""
        return jsonify({"status":"ok"})

    # @app.errorhandler(404)
    # def page_not_found(e):
    #     return 404 template