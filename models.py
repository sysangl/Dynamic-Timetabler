
# types
import uuid, zoneinfo,time
from datetime import datetime
from typing import List, Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.sqlite import (
    DATETIME,
    JSON,
    INTEGER
)
# from sqlalchemy.dialects.postgresql import (
#     UUID,
#     ARRAY,
#     TIMESTAMP,
#     INTEGER
# )

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
    id : Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    title : Mapped[str] = mapped_column(nullable=False)
    completed : Mapped[bool] = mapped_column(nullable=False, default=False)

    def __init__(self, title : str) -> None:
        super().__init__()
        self.title = title


    def serialise(self)->dict:
        return {
            'id' : str(self.id),
            'title' : self.title,
            'completed' : self.completed,
        }

class Task(ToDo):
    """
    A ToDo with more information and can be set for a certain date and time
    """
    description : Mapped[str] = mapped_column(default="")
    # postgreSQL - Production
    #start_datetime : Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    # sqlite - Dev
    start_datetime : Mapped[datetime] = mapped_column(DATETIME, nullable=False)
    reschedule : Mapped[bool] = mapped_column(nullable=False, default=False)
    def __init__(self, 
                title:str, 
                start_datetime: datetime,
                description:str = "", 
                ) -> None:
        super().__init__(title)
        self.description = description
        self.start_datetime = start_datetime


    def serialise(self)->dict:
        return {
            'id' : str(self.id),
            'title' : self.title,
            'description' : str(self.description),
            'completed' : self.completed,
            'start_datetime' : self.start_datetime,
        }
class Block(Task):
    """
    Occupies a span of time.
    """
    end_datetime : Mapped[datetime] = mapped_column(DATETIME, nullable=False)
    def __init__(self, 
                title:str, 
                start_datetime: dict,
                end_datetime: dict,
                description:str = "", 
                ) -> None:
        super().__init__(title=title, start_datetime=datetime(**start_datetime), description=description)
        # postgreSQL - Production
        #end_datetime : Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
        # sqlite - Dev
        self.end_datetime = datetime(**end_datetime)
    
    def serialise(self)->dict:
        return {
            'id' : str(self.id),
            'title' : self.title,
            'completed' : self.completed,
            'description' : str(self.description),
            'start_datetime' : self.start_datetime,
            'end_datetime' : self.end_datetime,
        }

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

    name : Mapped[str] = mapped_column(nullable=False, default="Untitled Activity")
    description : Mapped[str] = mapped_column(nullable=False, default="")
    # set the priority of this acitivity
    # lower priority means this activity's blocks can be moved around
    priority : Mapped[int] = mapped_column(nullable = False,default=0)

    # 0 - no repeat/oneshot
    # 1 - repeat every X
    # 2 - use frequency
    repeat_mode : Mapped[int] = mapped_column(nullable = False,default=0)

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

    def __init__(self,
                name:str,
                description:str="",
                priority:int=0,
                repeat_mode:int=0,
                repeat_interval:list[int]=[0,0,0,0,0],
                frequency:list[int]=[0,0,0,0,0],
                even_frequency_spacing:bool=True,
                min_length:int=45,
                max_length:int=-1,
                min_time:int=-1,
                max_time:int=-1,
                time_limit_reset:list[int]=[0,0,0,0,0],
                **extra
                ) -> None:
        super().__init__()
        self.name = name
        self.description = description
        self.priority = priority
        self.repeat_mode = repeat_mode
        self.repeat_interval = repeat_interval
        self.frequency = frequency
        self.even_frequency_spacing = even_frequency_spacing
        self.min_length = min_length
        self.max_length = max_length
        self.min_time = min_time
        self.max_time = max_time
        self.time_limit_reset = time_limit_reset
        self.extra = extra



    def serialise(self)->dict:
        return {
            'id' : self.id,
            'name' : self.name,
            'description' : self.description,
            'priority' : self.priority,
            'repeat_mode' : self.repeat_mode,
            'repeat_interval' : self.repeat_interval,
            'frequency' : self.frequency,
            'even_frequency_spacing' : self.even_frequency_spacing,
            'min_length' : self.min_length,
            'max_length' : self.max_length,
            'min_time' : self.min_time,
            'max_time' : self.max_time,
            'time_limit_reset' : self.time_limit_reset,
            'time_spent' : self.time_spent
        }

# i wanted to name this 'Class' but that would probably confusing for me
# class Subject(Activity):
#     teacher : Mapped[str] = mapped_column(nullable=False)
#     classroom : Mapped[Optional[str]] = mapped_column()



# Settings
#
#

class Settings(db.Model):
    """
    The user's preferences and settings
    Has one-to-one relationship with User table
    """
    id : Mapped[int] = mapped_column(INTEGER, primary_key=True,autoincrement=True)
    default_block_length : Mapped[int] = mapped_column(default=30) # minutes
    starting_day : Mapped[int] = mapped_column(default=0)
    starting_hour : Mapped[int] = mapped_column(default=5)

    user: Mapped["User"] = relationship(
        "User",
        back_populates="settings",
        uselist=False,          # one‑to‑one
        foreign_keys="[User.settings_id]",
        remote_side="[User.settings_id]"
    )

    __tablename__ = "settings"
    def __init__(self,
                default_block_length :int = 30,
                starting_day:int = 0,
                starting_hour:int = 5
                ) -> None:
        super().__init__()
        self.default_block_length = default_block_length
        self.starting_day = starting_day
        self.starting_hour = starting_hour



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
    """
    Stores users, so multiple people can use the same server to store different timetables.
    Has a one-to-one relationship with Settings table
    """


    __tablename__ = "users"
    id : Mapped[int] = mapped_column(INTEGER,primary_key=True, autoincrement=True)
    username : Mapped[str] = mapped_column(nullable=False, unique=True)
    display_name : Mapped[Optional[str]] = mapped_column(ForeignKey("settings.id", ondelete="CASCADE"))
    is_admin : Mapped[bool] = mapped_column(nullable=False, default=False)

    settings_id : Mapped[int] = mapped_column(
        INTEGER, 
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

    def __init__(self,
                username : str,
                display_name : str | None = None,
                is_admin : bool = False,
                ) -> None:
        super().__init__()
        self.username = username
        self.display_name = display_name or username
        self.is_admin = is_admin
        self.settings = Settings()

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
        }