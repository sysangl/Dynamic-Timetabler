from flask import Flask, jsonify, request, Blueprint
from flask_login import login_required, current_user

from app.models import (
    db,
    User,
    Settings
)
import logging

bp = Blueprint('settings', __name__)

db_logger = logging.getLogger("database")
app_logger = logging.getLogger("app")


def create_routes(app: Flask):

    @bp.route('/update', methods=['POST'])
    @login_required
    def update_settings():
        """
        Expected JSON (any subset of fields is valid)
        {
            "default_block_length": 45,
            "starting_day": 0,
            "starting_hour": 5,
        }
        """
        user_id = current_user.id

        app.logger.info("Attempting to update settings")
        app.logger.info(f"Recieved - {request.data}")
        app_logger.info(f"Attempting to update settings for User {user_id}")

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
        except Exception:
            db.session.rollback()
            db_logger.exception(f'Database error while updating settings for User (id:{user_id})')
            return jsonify({"error":"Database error while updating settings"}), 500
        app_logger.info(f'Successfully updated settings for User (id:{user_id})')
        return jsonify({"settings":settings.serialise()}), 200

    @bp.route('/', methods=['GET'])
    @login_required
    def get_settings():
        """
        Returns the user's settings
        """
        user_id = current_user.id
        app_logger.info(f"Fetching settings for User {user_id}")
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return jsonify({"error": f"User {user_id} not found"}), 404

        settings : Settings = user.settings
        payload = settings.serialise()

        return jsonify({"settings":payload})

