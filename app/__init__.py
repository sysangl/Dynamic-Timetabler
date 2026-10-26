import secrets
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from flask import Flask
from flask_migrate import Migrate

from helpers.config import _get_data_dir, get_config
from helpers.paths import resource_path

from .extensions import db, login_manager, pwd_hasher

__all__ = ['create_app']

def _default_config():
    cfg = dict(get_config())
    data_dir: Path = _get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    db_file = data_dir / 'database.sqlite'
    cfg.setdefault('SQLALCHEMY_DATABASE_URI', f'sqlite:///{db_file.resolve().as_posix()}')
    cfg.setdefault('SECRET_KEY', secrets.token_hex(32))
    cfg.setdefault('SESSION_COOKIE_HTTPONLY', True)
    cfg.setdefault('SESSION_COOKIE_SAMESITE', "Lax")
    cfg.setdefault('ARGON2_HASH_LENGTH', 32)
    cfg.setdefault('ARGON2_TIME_COST', 2)
    cfg.setdefault('ARGON2_MEMORY_COST', 64 * 1024)
    cfg.setdefault('ARGON2_PARALLELISM', 1)
    return cfg

def create_app(config: Mapping[str, Any] | None = None):
    app = Flask(
        "Canopy", 
        template_folder=resource_path('templates'), 
        static_folder=resource_path('static')
        )

    app.config.from_mapping(_default_config() if config is None else dict(config))
    
    db.init_app(app)
    pwd_hasher.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login" # type: ignore
    Migrate(app,db)

    with app.app_context():
        db.create_all()

    from .routes import initialise_routes
    initialise_routes(app)
    
    return app
