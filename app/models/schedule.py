from __future__ import annotations

import uuid
from datetime import datetime

import pytz
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db, db_logger
from .user import User

class Activity(db.Model):
    """
    Base Activity that drives auto timetable generation
    """
    __tablename__ = "activities"
    id : Mapped[uuid.UUID] = mapped_column(Uuid, primary_key = True, default=uuid.uuid4)
    group_name : Mapped[str] = mapped_column(nullable=False, default='default')

    name : Mapped[str] = mapped_column(nullable=False, default="Untitled Activity")
    description : Mapped[str] = mapped_column(nullable=False, default="")
    priority : Mapped[int] = mapped_column(nullable = False,default=0)
    frequency : Mapped[int] = mapped_column(default=0)
    even_frequency_spacing : Mapped[bool] = mapped_column(default=True)

    # min_length : Mapped[int | None] = mapped_column()
    max_length : Mapped[int] = mapped_column(default=0)
    min_time : Mapped[int] = mapped_column(default=0)
    # max_time : Mapped[int | None] = mapped_column()

    # is the start/end time fixed?
    # fixed_start : Mapped[bool] = mapped_column()
    # fixed_end : Mapped[bool] = mapped_column()
    fixed : Mapped[list[tuple[int, int, int]]] = mapped_column(JSON, default=list())  # noqa: C408

    time_limit_reset : Mapped[list[int]] = mapped_column(JSON, default=lambda: [0,0,0,0,0])

    time_spent : Mapped[int] = mapped_column(default=0)

    preferred_days : Mapped[list[int]] = mapped_column(JSON, default=list()) # type: ignore

    owner_id : Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner : Mapped[User] = relationship(
        "User",
        back_populates="activities"
    )

    blocks = relationship(
        "Block",
        back_populates="activity",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    colour : Mapped[str] = mapped_column(nullable=False, default="#75547e")
    def __init__(self,
                name:str,
                owner:User,
                description:str="",
                priority:int=0,
                frequency:int=0,
                even_frequency_spacing:bool=True,
                min_length:int=45,
                max_length:int=0,
                min_time:int=0,
                max_time:int=-1,
                preferred_days:list[int]=list(),  # noqa: B006
                time_limit_reset:list[int]|None=None,
                group_name: str = 'default',
                colour:str = '#75547e',
                **extra
                ) -> None:
        if time_limit_reset is None:
            time_limit_reset = [0, 0, 0, 0, 0]
        if frequency is None:
            frequency = []
        try:
            super().__init__()
            self.name = name
            self.owner = owner
            self.group_name = group_name
            self.description = description
            self.priority = priority
            self.frequency = frequency
            self.even_frequency_spacing = even_frequency_spacing
            # self.min_length = min_length
            self.max_length = max_length
            self.min_time = min_time
            # self.max_time = max_time
            # self.time_limit_reset = time_limit_reset
            self.extra = extra
            self.preferred_days: list[int] = preferred_days
            self.colour=colour


        except Exception:
            db_logger.exception("Failed to create Activity instance")
            raise

    def serialise(self)->dict:
        return {
            'id' : self.id,
            'group_name' : self.group_name,
            'title' : self.name,
            'description' : self.description,
            'priority' : self.priority,
            'frequency' : self.frequency,
            'even_frequency_spacing' : self.even_frequency_spacing,
            # 'min_length' : self.min_length,
            'max_length' : self.max_length,
            'min_time' : self.min_time,
            # 'max_time' : self.max_time,
            'time_limit_reset' : self.time_limit_reset,
            'time_spent' : self.time_spent,
            'colour': self.colour,
            'block_count' : len(self.blocks.all())
        }

class Schedule(db.Model):
    __tablename__ = "schedules"
    id : Mapped[uuid.UUID] = mapped_column(Uuid, primary_key = True, default=uuid.uuid4)
    group_name : Mapped[str] = mapped_column(nullable=False, default='default')

    name : Mapped[str] = mapped_column(nullable=False, default="Untitled Activity")
    description : Mapped[str] = mapped_column(nullable=False, default="")

    activities_to_blocks : Mapped[dict[int, int]] = mapped_column(JSON, default=dict())
    table : Mapped[list[list[int]]] = mapped_column(JSON,default=list())