"""
API routes related to users
"""

import logging

from flask import Blueprint, jsonify, request

from app.models import User, db
from helpers.server import _json_error, _json_success

bp = Blueprint('users', __name__)

log = logging.getLogger('app')

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
    log.info("Attempting to create user")
    log.info(f"Recieved - {request.data}")
    payload = request.get_json(silent=False)
    if not payload:
        log.info("User creation failed - Missing JSON body")
        log.info("User creation failed - Missing JSON body")
        return _json_error("Missing JSON body", 400)

    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        log.info("User creation failed - No username or password")
        log.info("User creation failed - No username or password")
        return _json_error("Field `username` and `password` is required", 400)

    # check if a user with that username already exists
    if User.query.filter_by(username=username).first():
        log.info("User creation failed - Username already taken")
        log.info("User creation failed - Username already taken")
        return _json_error(f"Username '{username}' already taken",409)

    log.info("Creating new user...")
    new_user = User(
        username=username, # type: ignore
        display_name=payload.get("display_name"), # type: ignore
    )
    new_user.password = password

    try:
        db.session.add(new_user)
        db.session.commit()
        return _json_success(new_user.serialise(), 201)
    except Exception:
        db.session.rollback()
        log.exception("Database error while creating user")
        return _json_error("Database error while creating user",500)

