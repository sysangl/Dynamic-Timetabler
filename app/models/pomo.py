from __future__ import annotations

import uuid
from datetime import datetime

import pytz
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db
from .schedule import Activity, Schedule
from .user import User


class Pomo(db.Model):
    __tablename__ = "pomos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_name: Mapped[str] = mapped_column(nullable=False, default="default")

    title: Mapped[str] = mapped_column(nullable=False)

    session_mins : Mapped[int] = mapped_column(default=45)
    break_mins : Mapped[int] = mapped_column(default=15)


    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner: Mapped[User] = relationship("User", back_populates="pomos")

    source: Mapped[str] = mapped_column(default="unknown")

    # activity_id: Mapped[uuid.UUID | None] = mapped_column(
    #     Uuid,
    #     ForeignKey("activities.id", ondelete="CASCADE"),
    #     index=True,
    # )

    # activity: Mapped[Activity] = relationship("Activity", back_populates="blocks")

    # schedule_id: Mapped[uuid.UUID | None] = mapped_column(
    #     Uuid,
    #     ForeignKey("schedules.id", ondelete="CASCADE"),
    #     index=True,
    # )

    # schedule: Mapped[Schedule] = relationship("Schedule", back_populates="blocks")


    def __init__(
        self,
        title: str,
        owner: User,
        session_mins:int = 45,
        break_mins:int =15,
        **extra,
    ) -> None:
        self.title = title
        self.owner = owner

    def serialise(self) -> dict:
        return {
            "id": str(self.id),
            "title": self.title,
            "session_mins": self.session_mins,
            "break_mins": self.break_mins,
            "owner": self.owner.id,
            "source": self.source
        }


