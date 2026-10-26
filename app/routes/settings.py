import logging

from flask import Blueprint, redirect, request, url_for
from flask_login import current_user, login_required

from helpers.server import _json_error, _json_success

from ..extensions import db
from ..models import Settings

bp = Blueprint('settings', __name__)

log = logging.getLogger("app")

@bp.route('/update', methods=['POST'])
@login_required
def update_settings():
    """
    Update the current user's settings.

    Example JSON : 
    {
        "default_block_length": 45,
        "start_day": 0,
        "start_hour": 5,
    }
    """
    user_id = current_user.id
    log.info("Attempting to update settings")
    log.info(f"Recieved - {request.form}")
    log.info(f"Attempting to update settings for User {user_id}")

    allowed_fields = {
        "default_block_length": int,
        "default_block_colour": str,
        "start_day": int,
        "start_hour": int,
        "timetable_view" : str,
        "days_per_view" : int,
    }

    settings : Settings = current_user.settings # type: ignore

    for key in request.form:
        if key not in allowed_fields:
            return _json_error(f"'{key}' is not a valid setting field.", 400)

        try:
            val = request.form.get(key)
            if not val : raise ValueError
            cast_val = allowed_fields[key](val)
        except (ValueError, TypeError):
            return _json_error(f"'{key}' is not a valid setting field", 400)
        setattr(settings, key, cast_val)

    log.info(f'Attempting to update settings for User:{current_user.username} (id:{user_id})')
    try:
        current_user.settings = settings
        db.session.commit()
    except Exception:
        db.session.rollback()
        log.exception(f'Database error while updating settings for User (id:{user_id})')
        return _json_error('Database error while updating settings', 500)
    log.info(f'Successfully updated settings for User:{current_user.username} (id:{user_id})')
    return redirect(url_for('app.serve_settings'))

@bp.route('/', methods=['GET'])
@login_required
def get_settings():
    """
    Returns the current user's settings
    """
    settings : Settings = current_user.settings
    return _json_success({"settings":settings.serialise()})

