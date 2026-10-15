from flask import Flask, jsonify, request
from models import (
    db,
    User,
    Settings
)



def create_routes(app: Flask):

    @app.route('/server/user/<int:user_id>/settings/update', methods=['POST'])
    def update_settings(user_id: int):
        """
        Expected JSON (any subset of fields is valid)
        {
            "default_block_length": 45,
            "starting_day": 0,
            "starting_hour": 5,
        }
        """

        app.logger.info("Attempting to update settings")
        app.logger.info(f"Recieved - {request.data}")

        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return jsonify({"error": f"User {user_id} not found"}), 404

        allowed_fields = {
            "default_block_length": int,
            "starting_day": int,
            "starting_hour": int,
        }

        payload = request.get_json(silent=False)
        if not payload:
            app.logger.info("User creation failed - Missing JSON body")
            return jsonify({"error": "Missing JSON body"}), 400

        settings : Settings = user.settings

        for key, value in payload.items():
            if key not in allowed_fields:
                return jsonify({"error" : f"'{key}' is not a valid setting field."}), 400

            try:
                cast_val = allowed_fields[key](value)
            except (ValueError, TypeError):
                return jsonify({"error" : f"'{key}' is not a valid seting field"}), 400

            setattr(settings, key, cast_val)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"error":"Database error while updating settings"}), 500

        return jsonify({"settings":settings.serialise()}), 200

    @app.route('/server/user/<int:user_id>/settings', methods=['GET'])
    def get_settings(user_id: int):
        """
        Returns the user's settings
        """
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return jsonify({"error": f"User {user_id} not found"}), 404

        settings : Settings = user.settings
        payload = settings.serialise()

        return jsonify({"settings":payload})

