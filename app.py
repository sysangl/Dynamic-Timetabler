import os, toml
from flask import Flask, request, jsonify, render_template, redirect, render_template_string
from flask_migrate import Migrate
from jinja2 import ChoiceLoader, FileSystemLoader
from sqlalchemy import create_engine
from route_init import initialise_routes
from models import (
    db
)
from config import Config

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

def create_app():
    with open("config/testing.toml", 'r') as f:
        config = toml.load(f)
    app = Flask("Dynamic Timetabler")
    #app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postgres@localhost:5432/dynamic_timetable"
    app.config["SQLALCHEMY_DATABASE_URI"] = config['database']['uri']
    assert app.jinja_loader is not None
    assert app.static_folder is not None
    app.jinja_env.loader = ChoiceLoader([
        app.jinja_loader,
        FileSystemLoader(app.static_folder)
        ])

    db.init_app(app)
    Migrate(app,db)


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


if __name__ == "__main__":
    Config.load_config("config/testing.toml")
    config = Config.config
    app = create_app()
    initialise_routes(app)
    app.run(debug=config['server']['debug'], host=config['server']['host'], port=config['server']['port'])
