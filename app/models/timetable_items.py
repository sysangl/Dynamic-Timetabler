from __future__ import annotations

import uuid
from datetime import datetime

import pytz
from sqlalchemy import JSON, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db, db_logger
from .user import User


class ToDo(db.Model):
    """
    The most basic thing, essentially just a ToDo list.
    """
    id : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title : Mapped[str] = mapped_column(nullable=False)
    completed : Mapped[bool] = mapped_column(nullable=False, default=False)

    def __init__(self, title : str) -> None:
        super().__init__()
        try:
            self.title = title
        except Exception:
            db_logger.exception("Failed to create ToDo instance")
            raise

    def serialise(self)->dict:
        return {
            'id' : str(self.id),
            'title' : self.title,
            'completed' : self.completed,
        }

class Task(db.Model):
    """
    A ToDo with more information and can be set for a certain date and time
    """
    id : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title : Mapped[str] = mapped_column(nullable=False)
    completed : Mapped[bool] = mapped_column(nullable=False, default=False)
    description : Mapped[str] = mapped_column(default="")
    start_datetime : Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reschedule : Mapped[bool] = mapped_column(nullable=False, default=False)
    def __init__(self, 
                title:str, 
                start_datetime: dict,
                description:str = "", 
                ) -> None:
        try:
            self.title = title
            self.description = description
            self.start_datetime = datetime(**start_datetime,tzinfo=pytz.timezone('UTC'))
        except Exception:
            db_logger.exception("Failed to create Task instance")
            raise

    def serialise(self)->dict:
        return {
            'id' : str(self.id),
            'title' : self.title,
            'description' : str(self.description),
            'completed' : self.completed,
            'start_datetime' : self.start_datetime.isoformat(),
        }
class Block(db.Model):
    """
    Occupies a span of time.
    """
    id : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title : Mapped[str] = mapped_column(nullable=False)
    completed : Mapped[bool] = mapped_column(nullable=False, default=False)
    description : Mapped[str] = mapped_column(default="")
    start_datetime : Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reschedule : Mapped[bool] = mapped_column(nullable=False, default=False)
    end_datetime : Mapped[datetime] = mapped_column(DateTime, nullable=False)
    colour : Mapped[str] = mapped_column(nullable=False, default="#75547e")
    owner_id : Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner : Mapped[User] = relationship(
        "User",
        back_populates="blocks"
    )

    start_date : Mapped[str] = mapped_column(default='')
    start_time : Mapped[str] = mapped_column(default='')
    end_date : Mapped[str] = mapped_column(default='')
    end_time : Mapped[str] = mapped_column(default='')

    def __init__(self, 
                title:str, 
                start_datetime: datetime,
                owner: User,
                end_datetime: datetime,
                description:str = "", 
                colour:str = "",
                start_date:str="",
                start_time:str="",
                end_date:str="",
                end_time:str="",
                **extra
                ) -> None:
        try:
            self.title = title
            self.description = description
            self.start_datetime = start_datetime
            self.end_datetime = end_datetime
            # self.multiday = self.start_datetime.date().isocalendar
            self.colour = colour
            self.owner = owner
            self.start_date = start_date
            self.start_time = start_time
            self.end_date = end_date
            self.end_time = end_time
        except Exception:
            db_logger.exception("Failed to create Block instance")
            raise

    def overlaps(self, block: Block)->bool:
        return max(self.start_datetime, block.start_datetime) < min(self.end_datetime, block.end_datetime)

    
    def serialise(self)->dict:
        return {
            'id' : str(self.id),
            'title' : self.title,
            'completed' : self.completed,
            'description' : str(self.description),
            'start_datetime' : self.start_datetime.isoformat(),
            'end_datetime' : self.end_datetime.isoformat(),
            'start_date': self.start_date,
            'start_time': self.start_time,
            'end_date' : self.end_date,
            'end_time' : self.end_time,
            'colour' : self.colour,
            'owner' : self.owner.id
        }

class Activity(db.Model):
    """
    Base Activity that drives auto timetable generation
    """
    __tablename__ = "activities"
    id : Mapped[uuid.UUID] = mapped_column(primary_key = True, default=uuid.uuid4)

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

    def __init__(self,
                name:str,
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
                **extra
                ) -> None:
        if time_limit_reset is None:
            time_limit_reset = [0, 0, 0, 0, 0]
        if frequency is None:
            frequency = []
        try:
            super().__init__()
            self.name = name
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


        except Exception:
            db_logger.exception("Failed to create Activity instance")
            raise

    def serialise(self)->dict:
        return {
            'id' : self.id,
            'name' : self.name,
            'description' : self.description,
            'priority' : self.priority,
            'frequency' : self.frequency,
            'even_frequency_spacing' : self.even_frequency_spacing,
            # 'min_length' : self.min_length,
            'max_length' : self.max_length,
            'min_time' : self.min_time,
            # 'max_time' : self.max_time,
            'time_limit_reset' : self.time_limit_reset,
            'time_spent' : self.time_spent
        }

class Routine(db.Model):
    __tablename__ = "routines"
    id : Mapped[uuid.UUID] = mapped_column(primary_key = True, default=uuid.uuid4)
    name : Mapped[str] = mapped_column(nullable=False, default="New Routine")

    start_date : Mapped[datetime] = mapped_column(nullable=False)
    end_date : Mapped[datetime | None] = mapped_column()

    # length of time the routine encompases and when it repeats. defaukt : a 7day routine that repeats every week
    routine_length : Mapped[int] = mapped_column(nullable=False, default=7)
    repeats_every : Mapped[int] = mapped_column(nullable=False, default=7)

    blocks : Mapped[list[Block]] = mapped_column(JSON, nullable=False)

    def __init__(self, 
                name,
                start_date,
                end_date = None,
                routine_length = 7,
                repeats_every = 7
                ) -> None:
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.routine_length = routine_length
        self.repeats_every = repeats_every
        self.blocks = []
        