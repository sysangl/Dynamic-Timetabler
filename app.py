# import os, toml, multiprocessing
import sys, os, logging
from flask import Flask, request, jsonify, render_template, redirect, render_template_string
from flask_migrate import Migrate
from flask_migrate.cli import upgrade as db_upgrade, init as db_init, migrate as db_migrate
from jinja2 import ChoiceLoader, FileSystemLoader
# from sqlalchemy import create_engine
# from route_init import initialise_routes
from models import (
    db
)
from helpers.config import get_config, reload_config
from pathlib import Path
from helpers.paths import resource_path

# For production
#engine = create_engine("postgresql://postgres:postgres@localhost:5432/dynamic_timetable")

def create_app():
    TEMPLATE_ROOT = resource_path('templates')
    STATIC_ROOT = resource_path('static')
    config = get_config()
    home_dir = Path.home()
    project_dir = home_dir / ".dynamic-timetabler"
    project_dir.mkdir(parents=True, exist_ok=True)
    db_file = project_dir / "dynamic-timetabler.sqlite"
    sqlite_uri = f"sqlite:///{db_file.resolve().as_posix()}"
    server_logger = logging.getLogger('server')

    app = Flask("Dynamic Timetabler", template_folder=TEMPLATE_ROOT, static_folder=STATIC_ROOT)

    #app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postgres@localhost:5432/dynamic_timetable"
    #app.config["SQLALCHEMY_DATABASE_URI"] = config['database']['uri']
    app.config["SQLALCHEMY_DATABASE_URI"] = sqlite_uri
    
    db.init_app(app)
    Migrate(app,db)


    server_logger.info(f"Starting a server on 'http://{config['server']['host']}:{config['server']['host']}'")

    app.logger.info( "=======================================================================")
    app.logger.info(r"        ___                             _                              ")     
    app.logger.info(r"       /   \_   _ _ __   __ _ _ __ ___ (_) ___                         ")
    app.logger.info(r"      / /\ / | | | '_ \ / _` | '_ ` _ \| |/ __|                        ")
    app.logger.info(r"     / /_//| |_| | | | | (_| | | | | | | | (__                         ")
    app.logger.info(r"    /___,'  \__, |_| |_|\__,_|_| |_| |_|_|\___|                        ")
    app.logger.info(r"            |___/                                                      ")
    app.logger.info(r"                  _____ _                _        _     _              ")
    app.logger.info(r"                 /__   (_)_ __ ___   ___| |_ __ _| |__ | | ___ _ __    ")
    app.logger.info(r"                   / /\/ | '_ ` _ \ / _ \ __/ _` | '_ \| |/ _ \ '__|   ")
    app.logger.info(r"                  / /  | | | | | | |  __/ || (_| | |_) | |  __/ |      ")
    app.logger.info(r"                  \/   |_|_| |_| |_|\___|\__\__,_|_.__/|_|\___|_|      ")
    app.logger.info(r"                                                                       ")
    app.logger.info(f" To open the web interface go to 'http://{config['server']['host']}:{config['server']['port']}/app/timetable ")
    app.logger.info( "=======================================================================")


    assert app.static_folder is not None
    assert app.jinja_loader is not None
    app.jinja_env.loader = ChoiceLoader([
        FileSystemLoader([TEMPLATE_ROOT,STATIC_ROOT])
        ])

    with app.app_context():
        db.create_all()
        # db_init(directory="migrations", template="flask")
        # db_migrate(message="initial", directory="migrations")
        # db_upgrade(directory="migrations")
        from models import User
        server_logger.info("Checking for default user")
        app.logger.info("Checking for default user")
        default_user = User.query.filter(User.username=="default_user").first()
        if not default_user:
            server_logger.info("Creating default user")
            app.logger.info("Creating default user")
            try:
                db.session.add(User(username="default_user", display_name="Default User"))
                db.session.commit()
            except Exception:
                server_logger.exception("Failed to create default user")
                app.logger.info("Failed to create default user")
                exit(-1)


    @app.route("/health")
    def health():
        """health-check ep"""
        return jsonify({"status":"ok"})

    @app.cli.command("list-tables")
    def list_tables():
        """for debugging, should print names of tables"""
        for table in db.metadata.sorted_tables:
            print(table.name)

    return app
