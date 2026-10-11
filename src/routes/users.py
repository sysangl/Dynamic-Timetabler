from flask import Flask, jsonify, request
from src.models import (
    db,
    ToDo,
    Task,
    Block,
    ClassBlock,
    Activity,
    Subject,
    User,
    Settings
)


def create_routes(app: Flask):
    """
    Create routes that deal with the user
    """

    @app.route('/server/user/create', methods=['POST'])
    def create_user():
        """
        Expected JSON (only "username" is required)
        {
            "username": "test_user",
            "display_name": "Test User",
        }
        """
        app.logger.info("Attempting to create user")
        app.logger.info(f"Recieved - {request.data}")
        payload = request.get_json(silent=False)
        if not payload:
            app.logger.info("User creation failed - Missing JSON body")
            return jsonify({"error": "Missing JSON body"}), 400

        username = payload.get("username")
        if not username:
            app.logger.info("User creation failed - No username")
            return jsonify({"error": "Field `username` is required"}), 400

        # check if a user with that username already exists
        if User.query.filter_by(username=username).first():
            app.logger.info("User creation failed - Username already taken")
            return (
                jsonify({"error": f"Username '{username}' already taken"}),
                409,
            ) # 409 is conflict coee

        app.logger.info("Creating new user...")
        new_settings=Settings(
            
        )
        new_user = User(
            username=username, # type: ignore
            display_name=payload.get("display_name"), # type: ignore
            settings=new_settings # type: ignore
        )

        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # make a logger later
            return jsonify({"error": "Database error while creating user", "details":str(e)}), 500

        return jsonify(new_user.serialise()), 201 # 201 success