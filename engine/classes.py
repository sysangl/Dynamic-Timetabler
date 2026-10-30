import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

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
    EVEN_SPACING = 5.0
    OVERLOAD = 3.0
    PRIORITY = 3.0
    IDLE = 3.0
    BALANCE = 20.0
    FRAGMENT = 8.0
    EARLY_BOUND = 200.0
    LATE_BOUND = 600.0
    HIGH_COST_BOUND = 300.0

class _Schedule:
    def __init__(self) -> None:
        self.table: Table = []



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
                frequency:int=1,
                even_spacing:bool = False,
                min_weekly_minutes: int = 0,
                max_block_minutes: int = 60,
                min_start_minutes: int = 0,
                fixed:list[tuple[int, int, int]]|None = None,
                priority:int = 1,
                ) -> None:
        
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
        # maximum length of time a single block can be
        self.max_block_minutes: int = max_block_minutes
        # minimum time this block can be placed at, e.g. only do 'Study' after 4pm
        self.min_start_minutes: int = min_start_minutes
        # activity priority, affects penalty calculations
        self.priority = priority
    
    @property
    def min_weekly_slots(self)->int:
        return math.ceil(self.min_weekly_minutes / _Schedule.SLOT_SIZE)
    
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

    # def _convert_to_db_block(self)->Block|None:
    #     return None
    #     b = Block(
    #     )
    #     return b