import math
import zoneinfo
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from helpers.config import get_config

from ..models import Activity, Block, User

type ATB = dict[int, set[int]]
type Table = list[list[int | None]]


@dataclass
class ChangeResult:
    delta: float
    undo: Callable
    mark_undo: bool = False

@dataclass
class LIMIT:
    HARD = math.inf
    HARD_SOFT = 10.0
    SOFT = 10.0
    NORMAL = 1.0

@dataclass
class PENALTY_WEIGHTS:
    MIN_TIME = 20.0
    FREQ = 2.0
    EVEN_SPACING = 10.0
    OVERLOAD = 3.0
    PRIORITY = 3.0
    IDLE = 3.0
    BALANCE = 20.0
    FRAGMENT = 8.0
    EARLY_BOUND = 200.0
    LATE_BOUND = 600.0
    HIGH_COST_BOUND = 300.0
    PREFERRED_DAYS = 30.0
    MIN_LENGTH = 20.0

class _Schedule:
    def __init__(self, owner: User) -> None:
        self.table: Table = []
        self.start_date : date = datetime.now(tz=zoneinfo.ZoneInfo(get_config()["general"]["timezone"])).date()
        self.owner : User = owner


    SIZE = 7
    MINS_IN_DAY = 24 * 60
    SLOT_SIZE = 10 #mins
    SLOTS_PER_DAY = MINS_IN_DAY//SLOT_SIZE
    EARLY = 6*60
    EARLY_SLOTS = EARLY//SLOT_SIZE

    LATE=22*60
    LATE_SLOTS = LATE//SLOT_SIZE

    HIGH_COST_BOUNDS:dict[int,list[tuple[int, int]]] = {  # noqa: RUF012
        6:[(9*60//SLOT_SIZE,12*60//SLOT_SIZE)]
    }

    def __call__(self, *args: Any, **kwds: Any) -> Table:
        return self.table

class _Activity:
    """
    Engine specific class for activities. Database Activities are converted to and from Engine _Activities
    """

    id_registry = -1

    def __init__(self,
                name:str,
                db_id,
                frequency:int=1,
                even_spacing:bool = False,
                min_weekly_minutes: int = 0,
                min_block_minutes: int = 60,
                max_block_minutes: int = 60,
                min_start_minutes: int = 0,
                fixed:list[tuple[int, int, int]]|None = None,
                preferred_days:list[int]|None = None,
                priority:int = 1,
                ) -> None:
        
        if preferred_days is None:
            preferred_days = []
        self.fixed:list[tuple[int, int, int]] = []
        if fixed is None:
            self.fixed = []
        else:
            self.fixed = fixed
        self.id:int = self.generate_id()
        # name of activity
        self.name : str = name
        # how many time it should appear in one timetable
        self.frequency:int = frequency
        # whether the algorithm should attempt to evenly spread out the blocks
        self.even_spacing:bool = even_spacing
        # minimum amount of time that must be allocated
        self.min_weekly_minutes: int = min_weekly_minutes
        self.min_block_minutes: int = min_block_minutes
        # maximum length of time a single block can be
        self.max_block_minutes: int = max_block_minutes
        # minimum time this block can be placed at, e.g. only do 'Study' after 4pm
        self.min_start_minutes: int = min_start_minutes
        # preferred days
        self.preferred_days: list[int] = preferred_days
        # activity priority, affects penalty calculations
        self.priority = priority

        self.db_id = db_id
    
    @property
    def min_weekly_slots(self)->int:
        return math.ceil(self.min_weekly_minutes / _Schedule.SLOT_SIZE)

    @property
    def min_block_slots(self)->int:
        return math.floor(self.min_block_minutes//_Schedule.SLOT_SIZE)
    
    @property
    def max_block_slots(self)->int:
        return max(1,self.max_block_minutes//_Schedule.SLOT_SIZE)

    @property
    def min_start_slot(self)->int:
        return math.floor(self.min_start_minutes / _Schedule.SLOT_SIZE)

    @property
    def fixed_blocks(self)->list[tuple[int, int, int]]:
        # convert fixed block minuts to slots
        output = []
        for day, start_mins, length_mins in self.fixed:
            start_slot = start_mins // _Schedule.SLOT_SIZE
            length = max(1, length_mins// _Schedule.SLOT_SIZE)
            output.append((day,start_slot, length))
        return output

    @classmethod
    def generate_id(cls)->int:
        cls.id_registry = cls.id_registry+1
        return cls.id_registry

    def __str__(self) -> str:
        return f"<_Activity {self.id}: {self.name}"


class _Block:
    id_registry = -1

    def __init__(self,
                activity_id:int,
                day:int,
                start:int,
                length:int,
                fixed: bool = False,
                id:int=-1
                ) -> None:
        if id < 0:
            self.id:int = self.generate_id()
        else:
            self.id:int = id
        # self.move_penalty: float
        self.activity_id: int=activity_id
        # the following uses engine specific units (slots) not minutes
        self.start:int=start
        self.length:int=length
        self.day:int=day
        self.fixed: bool = fixed

    @classmethod
    def generate_id(cls)->int:
        cls.id_registry = cls.id_registry+1
        return cls.id_registry

    def __str__(self) -> str:
        return f"<Block {self.id}: _Activity {self.activity_id}>"

def engine_to_db_blocks(schedule: _Schedule, blocks:dict[int, _Block], atb:ATB, activities:list[_Activity])->list[Block]:
    db_blocks:list[Block] = []
    from helpers.config import get_config
    for a in activities:
        for bid in atb[a.id]:
            b = blocks[bid]
            tz = get_config()["general"]["timezone"]
            start_hours = math.floor(b.start*_Schedule.SLOT_SIZE/60)
            start_time = (b.start*_Schedule.SLOT_SIZE)%60
            start_datetime = datetime(schedule.start_date.year, schedule.start_date.month, schedule.start_date.day, start_hours, start_time, tzinfo=zoneinfo.ZoneInfo(tz)) + timedelta(days=b.day)
            length_hours = (b.length*_Schedule.SLOT_SIZE)//60
            length_mins = (b.length*_Schedule.SLOT_SIZE)%60
            end_datetime = start_datetime + timedelta(hours=length_hours, minutes=length_mins)
            dbb = Block(
                title=a.name,
                owner=schedule.owner,
                start_datetime=start_datetime,
                end_datetime=end_datetime
                # start_date=start_datetime.date().isoformat(),
                # start_time=start_datetime.time().isoformat()[0:4]
            )
            dbb.activity_id = a.db_id
            db_blocks.append(dbb)
    return db_blocks

def db_to_engine_activities(activities: list[Activity])->list[_Activity]:
    engine_activities = []
    for a in activities:
        ea = _Activity(
            name=a.name,
            frequency=a.frequency,
            even_spacing=a.even_frequency_spacing,
            min_weekly_minutes=a.min_time,
            max_block_minutes=a.max_length,
            min_start_minutes=a.min_start_time,
            fixed=a.fixed,
            preferred_days=a.preferred_days,
            priority=a.priority,
            db_id=a.id
        )
        engine_activities.append(ea)
    return engine_activities