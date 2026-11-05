import math
import uuid
import zoneinfo
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from helpers.config import get_config

from ..models import Activity, Block, Schedule, User

type ATB = dict[int, set[int]]
type Table = list[list[int | None]]
type OverlapTable = list[list[set]]


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
    # User defined
    LATE_BOUND      = 60.0
    EARLY_BOUND     = 20.0
    MIN_TIME        = 8.0
    FREQ            = 7.0
    EVEN_SPACING    = 9.0
    OVERLOAD        = 4.0
    PRIORITY        = 8.0
    HIGH_COST_BOUND = 18.0
    PREFERRED_DAYS  = 14.0
    MIN_LENGTH      = 30.0


    # Timetable
    IDLE            = 1.0
    BALANCE         = 2.0
    FRAGMENT        = 4.0


class _Schedule:
    MINS_IN_DAY = 24 * 60

    def __init__(
        self,
        db_id: uuid.UUID,
        owner: User,
        start_date: date,
        size: int = 7,
        slot_size: int = 10,
        early: int = 360,
        late: int = 1320,
    ) -> None:
        self.db_id = db_id
        self.table: OverlapTable = []
        self.start_date: date = start_date
        self.owner: User = owner
        self.SIZE = size
        self.SLOT_SIZE = slot_size
        self.SLOTS_PER_DAY = self.MINS_IN_DAY // self.SLOT_SIZE
        self.EARLY = early
        self.EARLY_SLOTS = self.EARLY // self.SLOT_SIZE

        self.LATE = late
        self.LATE_SLOTS = self.LATE // self.SLOT_SIZE

        self.HIGH_COST_BOUNDS: dict[int, list[tuple[int, int]]] = {
            6: [(9 * 60 // self.SLOT_SIZE, 12 * 60 // self.SLOT_SIZE)]
        }
        self.OVERLAP_PRIORITIES = {6,7,8,9,10}

    def __call__(self, *args: Any, **kwds: Any) -> OverlapTable:
        return self.table


class _Activity:
    """
    Engine specific class for activities. Database Activities are converted to and from Engine _Activities
    """

    id_registry = -1

    def __init__(
        self,
        name: str,
        db_id,
        schedule: _Schedule,
        frequency: int = 1,
        even_spacing: bool = False,
        min_weekly_minutes: int = 0,
        min_block_minutes: int = 60,
        max_block_minutes: int = 60,
        min_start_minutes: int = 0,
        fixed: list[tuple[int, int, int]] | None = None,
        preferred_days: list[int] | None = None,
        priority: int = 1,
    ) -> None:

        if preferred_days is None:
            preferred_days = []
        self.fixed: list[tuple[int, int, int]] = []
        if fixed is None:
            self.fixed = []
        else:
            self.fixed = fixed
        self.id: int = self.generate_id()
        # name of activity
        self.name: str = name
        # how many time it should appear in one timetable
        self.frequency: int = frequency
        # whether the algorithm should attempt to evenly spread out the blocks
        self.even_spacing: bool = even_spacing
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
        self.schedule = schedule
        self.db_id = db_id

    @property
    def min_weekly_slots(self) -> int:
        return math.ceil(self.min_weekly_minutes / self.schedule.SLOT_SIZE)

    @property
    def min_block_slots(self) -> int:
        return math.floor(self.min_block_minutes // self.schedule.SLOT_SIZE)

    @property
    def max_block_slots(self) -> int:
        return max(1, self.max_block_minutes // self.schedule.SLOT_SIZE)

    @property
    def min_start_slot(self) -> int:
        return math.floor(self.min_start_minutes / self.schedule.SLOT_SIZE)

    @property
    def fixed_blocks(self) -> list[tuple[int, int, int]]:
        # convert fixed block minuts to slots
        output = []
        for day, start_mins, length_mins in self.fixed:
            start_slot = start_mins // self.schedule.SLOT_SIZE
            length = max(1, length_mins // self.schedule.SLOT_SIZE)
            output.append((day, start_slot, length))
        return output

    @classmethod
    def generate_id(cls) -> int:
        cls.id_registry = cls.id_registry + 1
        return cls.id_registry

    def __str__(self) -> str:
        return f"<_Activity {self.id}: {self.name}"


class _Block:
    id_registry = -1

    def __init__(
        self,
        activity_id: int,
        day: int,
        start: int,
        length: int,
        fixed: bool = False,
        id: int = -1,
    ) -> None:
        if id < 0:
            self.id: int = self.generate_id()
        else:
            self.id: int = id
        # self.move_penalty: float
        self.activity_id: int = activity_id
        # the following uses engine specific units (slots) not minutes
        self.start: int = start
        self.length: int = length
        self.day: int = day
        self.fixed: bool = fixed

    @classmethod
    def generate_id(cls) -> int:
        cls.id_registry = cls.id_registry + 1
        return cls.id_registry

    def __str__(self) -> str:
        return f"<Block {self.id}: _Activity {self.activity_id}>"


def engine_to_db_blocks(
    schedule: _Schedule,
    blocks: dict[int, _Block],
    atb: ATB,
    activities: list[_Activity],
) -> list[Block]:
    db_blocks: list[Block] = []
    for a in activities:
        for bid in atb[a.id]:
            b = blocks[bid]
            tz = get_config()["general"]["timezone"]
            start_hours = math.floor(b.start * schedule.SLOT_SIZE / 60)
            start_time = (b.start * schedule.SLOT_SIZE) % 60
            start_datetime = datetime(
                schedule.start_date.year,
                schedule.start_date.month,
                schedule.start_date.day,
                start_hours,
                start_time,
                tzinfo=zoneinfo.ZoneInfo(tz),
            ) + timedelta(days=b.day)
            length_hours = (b.length * schedule.SLOT_SIZE) // 60
            length_mins = (b.length * schedule.SLOT_SIZE) % 60
            end_datetime = start_datetime + timedelta(
                hours=length_hours, minutes=length_mins
            )
            dbb = Block(
                title=a.name,
                owner=schedule.owner,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                # start_date=start_datetime.date().isoformat(),
                # start_time=start_datetime.time().isoformat()[0:4]
            )
            dbb.activity_id = a.db_id
            dbb.schedule_id = schedule.db_id
            db_blocks.append(dbb)
    return db_blocks


def db_to_engine_activities(
    schedule: _Schedule, activities: list[Activity]
) -> list[_Activity]:
    engine_activities = []
    for a in activities:
        ea = _Activity(
            name=a.name,
            frequency=a.frequency,
            even_spacing=a.even_frequency_spacing,
            min_weekly_minutes=a.min_time,
            min_block_minutes=a.min_length,
            max_block_minutes=a.max_length,
            min_start_minutes=a.min_start_time,
            fixed=a.fixed,
            preferred_days=a.preferred_days,
            priority=a.priority,
            schedule=schedule,
            db_id=a.id,
        )
        engine_activities.append(ea)
    return engine_activities


def db_to_engine_schedule(schedule: Schedule) -> _Schedule:
    engine_schedule = _Schedule(
        db_id=schedule.id,
        owner=schedule.owner,
        start_date=schedule.start_date,
        size=schedule.length,
        slot_size=schedule.slot_size,
        early=schedule.early,
        late=schedule.late,
    )

    return engine_schedule
