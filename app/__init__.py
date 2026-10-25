# import os, toml, multiprocessing
import sys, os, logging, secrets
from flask import Flask, request, jsonify, render_template, redirect, render_template_string
from flask_migrate import Migrate
from flask_migrate.cli import upgrade as db_upgrade, init as db_init, migrate as db_migrate
from jinja2 import ChoiceLoader, FileSystemLoader
# from sqlalchemy import create_engine
# from route_init import initialise_routes
from app.models import (
    db, pwd_hasher
)
from helpers.config import get_config, reload_config, _get_data_dir
from pathlib import Path
from helpers.paths import resource_path
from app.routes.auth import login_manager

# For production
#engine = create_engine("postgresql://postgres:postgres@localhost:5432/dynamic_timetable")

def create_app():
    TEMPLATE_ROOT = resource_path('templates')
    STATIC_ROOT = resource_path('static')
    config = get_config()
    project_dir = _get_data_dir()
    project_dir.mkdir(parents=True, exist_ok=True)
    db_file = project_dir / "database.sqlite"
    sqlite_uri = f"sqlite:///{db_file.resolve().as_posix()}"
    server_logger = logging.getLogger('server')

    app = Flask("Canopy", template_folder=TEMPLATE_ROOT, static_folder=STATIC_ROOT)

    # APP CONFIGS ==============================

    # DATABASE
    #app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postgres@localhost:5432/dynamic_timetable"
    #app.config["SQLALCHEMY_DATABASE_URI"] = config['database']['uri']
    app.secret_key = secrets.token_hex(32) if not config['server']['debug'] else 'debug'
    app.config.update(
        SQLALCHEMY_DATABASE_URI = sqlite_uri,
        # ARGON (HASHING)
        ARGON2_HASH_LENGTH = 32,
        ARGON2_TIME_COST = 2,
        ARGON2_MEMORY_COST = 64 * 1024,
        ARGON2_PARALLELISM = 1,
    )
    
    db.init_app(app)
    pwd_hasher.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login" # type: ignore
    Migrate(app,db)
    
    server_logger.info(f"Starting a server on 'http://{config['server']['host']}:{config['server']['host']}'")

    assert app.static_folder is not None
    assert app.jinja_loader is not None
    app.jinja_env.loader = ChoiceLoader([
        FileSystemLoader([TEMPLATE_ROOT,STATIC_ROOT])
        ])

    with app.app_context():
        db.create_all()

    from .routes import initialise_routes
    initialise_routes(app)

    @app.cli.command("list-tables")
    def list_tables():
        """for debugging, should print names of tables"""
        for table in db.metadata.sorted_tables:
            print(table.name)

    return app
