# import os, toml, multiprocessing
import sys, os
from flask import Flask, request, jsonify, render_template, redirect, render_template_string
from flask_migrate import Migrate
from flask_migrate.cli import upgrade as db_upgrade, init as db_init, migrate as db_migrate
from jinja2 import ChoiceLoader, FileSystemLoader
# from sqlalchemy import create_engine
# from route_init import initialise_routes
from models import (
    db
)
from config import Config
from pathlib import Path
from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

# For production
#engine = create_engine("postgresql://postgres:postgres@localhost:5432/dynamic_timetable")

def resource_path(relative_path):
    """
    Return the absolute path to a resource, whether the app is
    running from a PyInstaller bundle or from source.
    """
    if getattr(sys, 'frozen', False):          # PyInstaller bundle
        base_path = sys._MEIPASS             # type: ignore # temporary extraction folder
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def create_app():
    TEMPLATE_ROOT = resource_path('templates')
    STATIC_ROOT = resource_path('static')
    home_dir = Path.home()
    project_dir = home_dir / ".dynamic-timetabler"
    project_dir.mkdir(parents=True, exist_ok=True)
    db_file = project_dir / "dynamic-timetabler.sqlite"
    sqlite_uri = f"sqlite:///{db_file.resolve().as_posix()}"

    app = Flask("Dynamic Timetabler", template_folder=TEMPLATE_ROOT, static_folder=STATIC_ROOT)
    #app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postgres@localhost:5432/dynamic_timetable"
    #app.config["SQLALCHEMY_DATABASE_URI"] = config['database']['uri']
    app.config["SQLALCHEMY_DATABASE_URI"] = sqlite_uri
    
    db.init_app(app)
    Migrate(app,db)
    with app.app_context():
        db.create_all()
        # db_init(directory="migrations", template="flask")
        # db_migrate(message="initial", directory="migrations")
        # db_upgrade(directory="migrations")
    

    assert app.static_folder is not None
    assert app.jinja_loader is not None
    app.jinja_env.loader = ChoiceLoader([
        FileSystemLoader([TEMPLATE_ROOT,STATIC_ROOT])
        ])


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
