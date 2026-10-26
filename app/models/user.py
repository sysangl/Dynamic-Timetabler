from __future__ import annotations

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db, db_logger, pwd_hasher
from .base import BaseModel


class Settings(db.Model):
    """
    The user's preferences and settings
    Has one-to-one relationship with User table
    """
    id : Mapped[int] = mapped_column(Integer, primary_key=True,autoincrement=True)
    default_block_length : Mapped[int] = mapped_column(default=30) # minutes
    default_block_colour : Mapped[str] = mapped_column(default="#155764") # minutes
    start_day : Mapped[int] = mapped_column(default=0)
    start_hour : Mapped[int] = mapped_column(default=0)
    timetable_view : Mapped[str] = mapped_column(default='horizontal')
    days_per_view : Mapped[int] = mapped_column(default=7) 

    user: Mapped[User] = relationship(
        "User",
        back_populates="settings",
        uselist=False,          # one‑to‑one
        foreign_keys="[User.settings_id]",
        remote_side="[User.settings_id]"
    )

    __tablename__ = "settings"
    def __init__(self,
                default_block_length :int = 30,
                start_day:int = 0,
                start_hour:int = 0
                ) -> None:
        try:
            super().__init__()
            self.default_block_length = default_block_length
            self.start_day = start_day
            self.start_hour = start_hour
        except Exception:
            db_logger.exception("Failed to create Settings instance")
            raise


    def serialise(self)->dict:
        return {
            "id": str(self.id),
            "default_block_length": self.default_block_length,
            "default_block_colour" : self.default_block_colour,
            "start_day": self.start_day,
            "start_hour": self.start_hour,
            "timetable_view": self.timetable_view,
            "days_per_view": self.days_per_view
        }

class User(db.Model):
    """
    Stores users, so multiple people can use the same server to store different timetables.
    Has a one-to-one relationship with Settings table
    """

    __tablename__ = "users"
    id : Mapped[int] = mapped_column(Integer,primary_key=True, autoincrement=True)
    username : Mapped[str] = mapped_column(nullable=False, unique=True)
    display_name : Mapped[str | None] = mapped_column(ForeignKey("settings.id", ondelete="CASCADE"))
    is_admin : Mapped[bool] = mapped_column(nullable=False, default=False)

    settings_id : Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("settings.id", ondelete="CASCADE"),
        nullable=False, 
        unique=True
    )
    settings : Mapped[Settings] = relationship(
        "Settings", 
        back_populates="user",
        single_parent=True,
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="[User.settings_id]",
        remote_side="[Settings.id]"
    )
    blocks = relationship(
        "Block",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    active: Mapped[bool] = mapped_column(default=True)


    @property
    def is_authenticated(self): 
        return True

    @property
    def is_active(self): 
        return getattr(self, "active", True)

    @property
    def is_anonymous(self): 
        return False

    def get_id(self):
        return str(self.id) 

    _password_hash: Mapped[str] = mapped_column(nullable=False)

    @property
    def password(self) -> str:
        raise AttributeError("Password hashes are write-only")

    @password.setter
    def password(self, plain_password: str) -> None:
        if not plain_password:
            raise ValueError("Password may not be empty")
        self._password_hash = pwd_hasher.generate_password_hash(plain_password)

    def verify_password(self, plain_password: str)->bool:
        if not self._password_hash:
            return False
        try:
            return pwd_hasher.check_password_hash(self._password_hash, plain_password)
        except Exception:
            db_logger.exception("Password verification failed")
            return False

    def __init__(self,
                username : str,
                display_name : str | None = None,
                is_admin : bool = False,
                ) -> None:
        try:
            super().__init__()
            self.username = username
            self.display_name = display_name or username
            self.is_admin = is_admin
            self.settings = Settings()
        except Exception:
            db_logger.exception("Failed to create User instance")
            raise


    # __table_args__ = (
    #     UniqueConstraint(
    #         "settings_id",
    #         name="uq_user_settings_id"   # <-- give the constraint a stable name
    #     ),
    # )

    def serialise(self) -> dict:
        return {
            "id" : self.id,
            "username": self.username,
            "display_name": self.display_name,
            "is_admin": self.is_admin,
            # embed the Settings payload (or ``None`` if it ever becomes optional)
            "settings": self.settings.serialise() if self.settings else None,
            #"no_of_blocks": self.blocks.all()
        }

