from flask import Flask, jsonify, request, Blueprint
from app.models import (
    db,
    User,
    Settings
)
import logging


bp = Blueprint('users', __name__)

app_logger = logging.getLogger('app')
db_logger = logging.getLogger('database')
def create_routes(app: Flask):

    @bp.route('/health',methods=['GET'])
    def user_healthcheck():
        return jsonify({'status':'ok'})


    @bp.route('/', methods=['GET'])
    def get_users():
        users = User.query.all()
        return jsonify({'users':[user.serialise() for user in users]}), 200

    @bp.route('/create', methods=['POST'])
    def create_user():
        """
        Expected JSON (only "username" & "password" is required)
        {
            "username": "test_user",
            "password": "password",
            "display_name": "Test User",
        }
        """
        #return jsonify({'msg':'Deprecated'}), 404
        app.logger.info("Attempting to create user")
        app.logger.info(f"Recieved - {request.data}")
        payload = request.get_json(silent=False)
        if not payload:
            app.logger.info("User creation failed - Missing JSON body")
            app_logger.info("User creation failed - Missing JSON body")
            return jsonify({"error": "Missing JSON body"}), 400

        username = payload.get("username")
        password = payload.get("password")
        if not username or not password:
            app.logger.info("User creation failed - No username or password")
            app_logger.info("User creation failed - No username or password")
            return jsonify({"error": "Field `username` and `password` is required"}), 400

        # check if a user with that username already exists
        if User.query.filter_by(username=username).first():
            app.logger.info("User creation failed - Username already taken")
            app_logger.info("User creation failed - Username already taken")
            return (
                jsonify({"error": f"Username '{username}' already taken"}),
                409,
            ) # 409 is conflict coee

        app.logger.info("Creating new user...")
        app_logger.info("Creating new user...")
        new_user = User(
            username=username, # type: ignore
            display_name=payload.get("display_name"), # type: ignore
        )
        new_user.password = password

        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db_logger.exception("Database error while creating user")
            return jsonify({"error": "Database error while creating user", "details":str(e)}), 500

        return jsonify(new_user.serialise()), 201 # 201 success