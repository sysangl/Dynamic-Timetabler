from __future__ import annotations

import uuid
from datetime import datetime

import pytz
from sqlalchemy import JSON, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db, db_logger
from .user import User


class Activity(db.Model):
    pass