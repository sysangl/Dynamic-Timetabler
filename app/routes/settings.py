from flask import Flask, jsonify, request, Blueprint, redirect, url_for
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
    def update():
        """
        Expected JSON (any subset of fields is valid)
        {
            "default_block_length": 45,
            "start_day": 0,
            "start_hour": 5,
        }
        """
        user_id = current_user.id
        app.logger.info("Attempting to update settings")
        app.logger.info(f"Recieved - {request.form}")
        app_logger.info(f"Attempting to update settings for User {user_id}")

        allowed_fields = {
            "default_block_length": int,
            "start_day": int,
            "start_hour": int,
            "timetable_view" : str,
            "days_per_view" : int,
        }

        settings : Settings = current_user.settings # type: ignore

        for key in request.form.keys():
            if key not in allowed_fields:
                return jsonify({"error" : f"'{key}' is not a valid setting field."}), 400

            try:
                val = request.form.get(key)
                if not val : raise ValueError
                cast_val = allowed_fields[key](val)
            except (ValueError, TypeError):
                return jsonify({"error" : f"'{key}' is not a valid setting field"}), 400
            setattr(settings, key, cast_val)

        db_logger.info(f'Attempting to update settings for User:{current_user.username} (id:{user_id})')
        try:
            current_user.settings = settings
            db.session.commit()
        except Exception:
            db.session.rollback()
            db_logger.exception(f'Database error while updating settings for User (id:{user_id})')
            return jsonify({"error":"Database error while updating settings"}), 500
        db_logger.info(f'Successfully updated settings for User:{current_user.username} (id:{user_id})')
        app_logger.info(f'Successfully updated settings for User:{current_user.username} (id:{user_id})')
        return redirect(url_for('app.serve_settings'))

    @bp.route('/', methods=['GET'])
    @login_required
    def get():
        """
        Returns the user's settings
        """
        user_id = current_user.id
        app_logger.info(f"Fetching settings for User {user_id}")
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return jsonify({"error": f"User {user_id} not found"}), 404

        settings : Settings = user.settings
        data = settings.serialise()

        return jsonify({"settings":data})

