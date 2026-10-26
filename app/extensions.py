from flask_argon2 import Argon2
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login" # type: ignore
pwd_hasher = Argon2()