import os, psycopg2
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from sqlalchemy import create_engine
from src.models import (
    db,
    ToDo,
    Task,
    Block,
    ClassBlock,
    Activity,
    Subject
)



#engine = create_engine("postgresql://postgres:postgres@localhost:5432/dynamic_timetable")


def create_app():
    app = Flask("Dynamic Timetabler")
    # os.getenv("DYNTIM_DATABASE_URI","")
    #app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postgres@localhost:5432/dynamic_timetable"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dynamic-timable.db"


    db.init_app(app)
    Migrate(app,db)

    @app.route("/")
    def serve_web_app():
        with open("./integrated-web/horizontal-view.html","r") as f:
            result = f.read()
        return result

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

app = create_app()




if __name__ == "__main__":
    app.run(debug=True)