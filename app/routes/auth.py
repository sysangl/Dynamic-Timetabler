import logging

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from app.models import User, db

bp = Blueprint("auth", __name__)

login_manager = LoginManager()

db_logger = logging.getLogger("database")
server_logger = logging.getLogger("server")

@login_manager.user_loader
def load_user(user_id:int) -> User | None:
    return User.query.get(user_id)

@bp.route('/register', methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    display_name = data.get("display_name")
    password = data.get("password")

    if not username or not password:
        return jsonify({'error':'Username & Password required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 409

    db_logger.info("Creating a new User")
    try:
        new_user = User(username=username,display_name=display_name)
        new_user.password = password
        db.session.add(new_user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        db_logger.exception("Database error while creating new User")
        return jsonify({'error':'Database error while creating new User'})
    db_logger.info(f'Created new User:{username} (id:{new_user.id})')
    return jsonify({'msg':'Registered new User', 'user_id':new_user.id}), 201

@bp.route('/login', methods=["GET","POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("app.dashboard"))

    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        next_url = request.args.get('next')

        server_logger.info(f'Attempting to login to {username}')

        user = User.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            login_user(user)
            flash("Welcome back!","success")
            server_logger.info(f'Logged into {username} (id:{user.id})')
            if not next_url or not next_url.startswith('/'):
                next_url = url_for('app.dashboard')
            return redirect(next_url)
        
        server_logger.info(f'Failed to login to {username}')
        flash("Invalid credentials", "danger")

    return render_template('login.html')

@bp.route("/logout")
@login_required
def logout():
    server_logger.info(f'Logging out user {current_user.username} (id:{current_user.id})')
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('auth.login'))

@login_manager.unauthorized_handler
def unauthorized():
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    wants_json = request.accept_mimetypes.best_match(
        ["application/json", "text/html"]
    ) == "application/json"
    has_json_flag = request.args.get("format") == "json"

    if is_ajax or wants_json or has_json_flag:
        return jsonify(error="authentication required"), 401

    login_url = url_for(login_manager.login_view, next=request.full_path) # type: ignore
    return redirect(login_url)