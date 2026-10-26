from flask_argon2 import Argon2
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
pwd_hasher = Argon2()