from flask import Flask, request, jsonify
import uuid
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


def initialise_routes(app: Flask):

    @app.route('/server/user/create', methods=['POST'])
    def create_user():
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
            username=username,
            display_name=payload.get("display_name"),
            settings=new_settings
        )

        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # make a logger later
            return jsonify({"error": "Database error while creating user", "details":str(e)}), 500

        return jsonify(new_user.serialise()), 201 # 201 success


    @app.route('/server/user/<int:user_id>/settings', methods=['GET'])
    def get_settings(user_id: int):
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return jsonify({"error": f"User {user_id} not found"}), 404

        settings : Settings = user.settings
        payload = settings.serialise()

        return jsonify({"settings":payload})



    # @app.route('/activities', methods=['GET'])
    # def get_activities():
    #     activities = Activity.query.all()
    #     return {'activities':[activity.serialize() for activity in activities]}

    # @app.route('/activities/<uuid:id>',methods=['GET'])
    # def get_activity(id):
    #     activity:Activity = Activity.query.filter_by(id=id).first()
    #     result = activity.serialize() if activity else -1
    #     return result


    # @app.route('/activities', methods=['POST'])
    # def create_activity():
    #     data = request.get_json()

    #     db.session.add(activity)
    #     db.session.commit()

    #     return jsonify(activity.serialize())

    # @app.route('/activities/<uuid:id>', methods=['PUT'])
    # def update_activity(id):
    #     pass

    # @app.route('/activities/<uuid:id>', methods=['DELETE'])
    # def delete_activity(id):
    #     pass