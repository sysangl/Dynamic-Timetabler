
# types
import uuid
from datetime import datetime
from typing import List, Optional

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.sqlite import (
    DATETIME,
    JSON,
)
from sqlalchemy.dialects.postgresql import (
    UUID,
    ARRAY,
    TIMESTAMP,
    INTEGER
)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)



# Time table blocking
# What appears on and what is stored in the timetable
#

class ToDo(db.Model):
    """
    The most basic thing, essentially just a ToDo list.
    """
    id : Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid6())
    title : Mapped[str] = mapped_column(nullable=False)

class Task(ToDo):
    """
    A ToDo with more information and can be set for a certain date and time
    """
    description : Mapped[str] = mapped_column(default="")
    # postgreSQL - Production
    #start_datetime : Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    # sqlite - Dev
    start_datetime : Mapped[datetime] = mapped_column(DATETIME, nullable=False)
    
class Block(Task):
    """
    Occupies a span of time.
    """
    # postgreSQL - Production
    #end_datetime : Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    # sqlite - Dev
    end_datetime : Mapped[datetime] = mapped_column(DATETIME, nullable=False)
    
class ClassBlock(Block):
    """
    
    """
    pass


# Activities
# For auto-generating timetables, blocks are created from these and their constraints
#

class Activity(db.Model):
    """
    Base Activity that drives auto timetable generation
    """
    __tablename__ = "activities"

    id : Mapped[uuid.UUID] = mapped_column(primary_key = True, default=uuid.uuid4)

    # set the priority of this acitivity
    # lower priority means this activity's blocks can be moved around
    priority : Mapped[int] = mapped_column(nullable = False)

    # 0 - no repeat/oneshot
    # 1 - repeat every X
    # 2 - use frequency
    repeat_mode : Mapped[int] = mapped_column(nullable = False)

    # repeat_interval -> [0,0,0,0,0]
    # repeat every [hour, day, week, month, year]
    # postgreSQL - Production
    #repeat_interval : Mapped[list[int]]= mapped_column(ARRAY(INTEGER), default=lambda: [0,0,0,0,0]) 
    # sqlite - Dev
    repeat_interval : Mapped[list[int]]= mapped_column(JSON, default=lambda: [0,0,0,0,0]) 
    

    # e.g. 2 times a week, 5 times a year
    # stored as [X, Y, Z]
    # means X times every Y Z's
    # for example [2, 1, 2] means, 2 times every 1 week.
    # Z values :
    # 0 - hours
    # 1 - days
    # 2 - weeks
    # 3 - months
    # 4 - years
    #
    # note: i will see how this system goes, if it is too messy, then i will just use
    #  an array [X,Y], Y will be the number of hours
    # this simpler approach may cause problems with detecting boundaries of, for example, each week
    # PostgreSQL - Production
    #frequency : Mapped[list[int]] = mapped_column(ARRAY(INTEGER), default=lambda: [0,0,0])
    # sqlite - Dev
    frequency : Mapped[list[int]] = mapped_column(JSON, default=lambda: [0,0,0])
        

    
    # try to evenly space frequencies, or just have multiple instances randomly
    # TRUE   |   FALSE
    # -      |   -
    # X      |   X
    # -      |   X
    # -      |   -
    # X      |   -
    # -      |   X
    # -      |   -
    # X      |   -
    # -      |   -
    even_frequency_spacing : Mapped[bool] = mapped_column(default=True)

    # the following are in minutes
    # minimum length of one block of this activity
    min_length : Mapped[Optional[int]] = mapped_column()
    # maximum length of one block of this activity
    max_length : Mapped[Optional[int]] = mapped_column()
    # minimum amount of time spenton the activity
    min_time : Mapped[Optional[int]] = mapped_column()
    # maximum time spent on activity
    # e.g. max game time of 4 hours total every day
    max_time : Mapped[Optional[int]] = mapped_column()


    # reset the time counter every [hour, day, week, month, year] 
    # PostgreSQL - for production
    #time_limit_reset : Mapped[list[int]] = mapped_column(ARRAY(INTEGER), default=lambda: [0,0,0,0,0])
    # sqlite - for dev
    time_limit_reset : Mapped[list[int]] = mapped_column(JSON, default=lambda: [0,0,0,0,0])


    # time spent doing this activity in minutes
    time_spent : Mapped[int] = mapped_column(default=0)

# i wanted to name this 'Class' but that would probably confusing for me
class Subject(Activity):
    teacher : Mapped[str] = mapped_column(nullable=False)
    classroom : Mapped[Optional[str]] = mapped_column()



# Settings
#
#

class Settings(db.Model):
    id : Mapped[uuid.UUID] = mapped_column(primary_key=True)
    default_block_length : Mapped[int] = mapped_column() # minutes
    starting_day : Mapped[int] = mapped_column(default=0)
    starting_hour : Mapped[int] = mapped_column(default=5)

    def serialise(self)->dict:
        return {
            "id": str(self.id),
            "default_block_length": self.default_block_length,
            "starting_day": self.starting_day,
            "starting_hour": self.starting_hour,
        }


# Other
#
#

class User(db.Model):
    id : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username : Mapped[str] = mapped_column(nullable=False, unique=True)
    display_name : Mapped[Optional[str]] = mapped_column(ForeignKey("settings.id", ondelete="CASCADE"))
    settings_id : Mapped[uuid.UUID] = mapped_column()
    settings : Mapped[Settings] = relationship("Settings", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def serialise(self) -> dict:
        return {
            "id" : self.id,
            "username": self.username,
            "display_name": self.display_name,
            # embed the Settings payload (or ``None`` if it ever becomes optional)
            "settings": self.settings.serialise() if self.settings else None,
        }