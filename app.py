import os, toml
from flask import Flask, request, jsonify, render_template, redirect, render_template_string
from flask_migrate import Migrate
from sqlalchemy import create_engine
from route_init import initialise_routes
from models import (
    db
)

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


def create_app(config:dict):
    app = Flask("Dynamic Timetabler")
    #app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postgres@localhost:5432/dynamic_timetable"
    app.config["SQLALCHEMY_DATABASE_URI"] = config['database']['uri']

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



def run(config_path: str = 'config/default.toml'):
    with open(config_path, 'r') as f:
        config = toml.load(f)
    app = create_app(config)

    initialise_routes(app)
    app.run(debug=config['server']['debug'], host=config['server']['host'], port=config['server']['port'])

if __name__ == "__main__":
    run("config/testing.toml")