import collections
import copy
import math
import random
from collections.abc import Callable
from dataclasses import dataclass

# from  import Block

type ATB = dict[int, set[int]]
type Table = list[list[int | None]]


@dataclass
class ChangeResult:
    delta: float
    undo: Callable

class LIMIT:
    HARD = math.inf
    HARD_SOFT = 10.0
    SOFT = 10.0
    NORMAL = 1.0

class PENALTY_WEIGHTS:
    MIN_TIME = 1.0
    FREQ = 2.0
    EVEN_SPACING = 2.0
    OVERLOAD = 3.0
    PRIORITY = 3.0
    IDLE = 4.0
    BALANCE = 3.0


MAX_PRIORITY = 10
# parameters
# DAYS = 7
SCHEDULE_SIZE = 7
MINS_IN_DAY = 24 * 60
SLOT_SIZE = 10 #mins
SLOTS_PER_DAY = MINS_IN_DAY//SLOT_SIZE

MAX_PRIORITY = 10
#penalty modifs

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
        return math.ceil(self.min_weekly_minutes / SLOT_SIZE)
    
    @property
    def max_block_slots(self)->int:
        return max(1,self.max_block_minutes//SLOT_SIZE)

    @property
    def min_start_slot(self)->int:
        return math.floor(self.min_start_minutes / SLOT_SIZE)

    @property
    def fixed_blocks(self)->list[tuple[int, int, int]]:
        # convert fixed block minuts to slots
        output = []
        for day, start_mins, length_mins in self.fixed:
            start_slot = start_mins // SLOT_SIZE
            length = max(1, length_mins//SLOT_SIZE)
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

def clamp(value, min_value, max_value):
    return max(min_value,min(value,max_value))

def clear_block(table:Table ,b:_Block):
    for slot in range(b.start, b.start + b.length):
        table[b.day][slot] = None

def find_free_slots(day:int, required_size: int, table:Table, start_from:int=0)->int | None:
    start = 0
    free_slots = 0
    row = table[day]
    for slot in range(start_from, len(row)):
        if row[slot] is None:
            if free_slots == 0:
                start=slot
            free_slots += 1
            if free_slots>=required_size:
                return start
        else:
            free_slots = 0
    return None

def allocate_lengths(needed:int, sessions:int, max_len:int)->list[int]:
    base_len = max(1, min(max_len, needed//sessions))
    lengths = [base_len] * sessions
    remaining = needed - base_len * sessions

    i=0
    while remaining > 0:
        if lengths[i] < max_len:
            lengths[i] += 1
            remaining -= 1
        i = (i+1)%sessions
        if i == 0 and all(l == max_len for l in lengths):
            break
    return lengths

def can_place(table:Table, b:_Block):
    for slot in range(b.start, b.start + b.length):
        if slot >= SLOTS_PER_DAY or not (0<=b.day<SCHEDULE_SIZE):
            return False
        if table[b.day][slot] not in {None, b.id}:
            return False
    return True

def place_block(table:Table, b: _Block):
    for slot in range(b.start, b.start + b.length):
        table[b.day][slot] = b.id

def schedule_activity(activity:_Activity, table:Table, blocks:dict[int, _Block], activity_to_blocks:ATB, day_load:list[int]):
    needed_sessions = max(activity.frequency, 1)

    total_needed = max(activity.min_weekly_slots, needed_sessions)

    lengths = allocate_lengths(total_needed, needed_sessions, activity.max_block_slots)
    used_days: set[int] = set()


    if activity.even_spacing:
        target_days = [min(max(0, round(i * SCHEDULE_SIZE / needed_sessions)), SCHEDULE_SIZE-1) for i in range(needed_sessions)]
    else:
        target_days = [None] * needed_sessions

    for idx, block_length in enumerate(lengths):
        candidate_days: list[int] = []
        if activity.even_spacing:
            ideal = target_days[idx]
            offsets = []
            for day in range(SCHEDULE_SIZE):
                offsets.append(day)
                offsets.append(-day)
            for offset in offsets:
                day = ideal + offset
                if 0<=day<SCHEDULE_SIZE and day not in used_days:
                    candidate_days.append(day)
            if not candidate_days:
                candidate_days = list(range(SCHEDULE_SIZE))

        else:
            activities_per_day = [
                (day, sum(1 for id in activity_to_blocks[activity.id] if blocks[id].day == day), day_load[day]) for day in range(SCHEDULE_SIZE)
            ]
            activities_per_day.sort(key=lambda x: (x[1],x[2]))
            candidate_days = [day for day,_,_ in activities_per_day]

        placed = False

        for day in candidate_days:
            free_slots_start = find_free_slots(day, block_length, table, start_from=activity.min_start_slot)
            if free_slots_start is not None:
                b = _Block(
                    activity_id=activity.id,
                    day=day,
                    start=free_slots_start,
                    length=block_length
                    )
                place_block(table, b)
                blocks[b.id] = b
                activity_to_blocks[activity.id].add(b.id)
                day_load[day] += 1
                used_days.add(day)
                placed = True
                break

        if not placed:
            for reduced_length in range(block_length-1, 0,-1):
                for day in candidate_days:
                    free_slots_start = find_free_slots(day, reduced_length, table, start_from=activity.min_start_slot)
                    if free_slots_start:
                        b = _Block(
                            activity_id=activity.id,
                            day=day,
                            start=free_slots_start,
                            length=reduced_length
                            )
                        place_block(table, b)
                        blocks[b.id] = b
                        activity_to_blocks[activity.id].add(b.id)
                        day_load[day] += 1
                        used_days.add(day)
                        placed = True
                        break
                if placed:
                    break

        if not placed:
            raise RuntimeError(f'Unable to place a block for activity {activity.id} with a length of {block_length}')


def place_fixed_blocks(table:Table, activities: list[_Activity], blocks: dict[int,_Block], activity_to_blocks:ATB, day_load:list[int]):
    for activity in activities:
        for day, start, length in activity.fixed_blocks:
            if length > activity.max_block_slots:
                raise ValueError(f'fixed block for activity {activity.id} exceeds the max size')

            b = _Block(
                activity_id=activity.id,
                day=day,
                start=start,
                length=length
            )
            if not can_place(table, b):
                raise ValueError(f'fixed block for activity {activity.id} overlaps another block')
                
            place_block(table, b)
            blocks[b.id] = b
            activity_to_blocks[activity.id].add(b.id)
            day_load[day] += 1

def greedy_initial(activities: list[_Activity], schedule_size:int=SCHEDULE_SIZE, slots_per_day:int=SLOTS_PER_DAY, slot_size:int=SLOT_SIZE):
    table: Table = [[None for _ in range(slots_per_day) ] for _ in range(SCHEDULE_SIZE)]
    blocks: dict[int, _Block] = {}
    activity_to_blocks:ATB = {}
    activity_to_blocks = {a.id: set() for a in activities}
    day_load:list[int] = [0]*SCHEDULE_SIZE

    place_fixed_blocks(table, activities, blocks, activity_to_blocks, day_load)

    sorted_activities = sorted(activities, key=lambda a: (a.priority, -int(a.even_spacing), -a.min_weekly_minutes))

    for a in sorted_activities:
        if len(a.fixed_blocks) >= a.frequency:
            continue
        schedule_activity(a, table, blocks, activity_to_blocks, day_load)

    return blocks, table, activity_to_blocks, day_load



saved_state = ()


class CostEvaluator:
    def __init__(self,
                activities: dict[int, _Activity],
                blocks: dict[int, _Block],
                atb: ATB,
                day_load: list[int]
                ) -> None:

        self.activities = activities
        self.blocks = blocks
        self.atb = atb
        self.day_load = day_load
        self.activity_cost = {a_id: self.calculate_cost(a_id) for a_id in self.activities}
        self.total_cost = sum(self.activity_cost.values())

    def calculate_cost(self, a_id:int):
        activity = self.activities[a_id]
        block_list = [self.blocks[bid] for bid in self.atb[a_id]]

        #cost for min time
        total_slots = sum(b.length for b in block_list)
        missing_time = max(0, activity.min_weekly_slots - total_slots)
        cost = missing_time * PENALTY_WEIGHTS.MIN_TIME

        #cost for frequency
        missing_freq = abs(len(block_list) - activity.frequency)
        cost += missing_freq * PENALTY_WEIGHTS.FREQ

        #cost for even spacing
        if activity.even_spacing and len(block_list) > 1:
            days = sorted(b.day for b in block_list)
            ideal = SCHEDULE_SIZE / activity.frequency
            # calcultaing standard error, spesh coming in clutch
            standard_err = sum((days[day+1]-days[day]-ideal) for day in range(len(days)-1))
            cost += standard_err**2 * PENALTY_WEIGHTS.EVEN_SPACING

        #cost for over load
        blocks_per_day = collections.Counter(b.day for b in block_list)
        target = math.ceil(activity.frequency/SCHEDULE_SIZE)
        for count in blocks_per_day.values():
            if count > target:
                cost += (count-target)**2 * PENALTY_WEIGHTS.OVERLOAD

        #cost for block size
        for block in block_list:
            if block.length > activity.max_block_slots:
                return LIMIT.HARD

        #scale w/ prio
        return cost * activity.priority

    def update_activities(self, activity_ids):
        delta = 0
        for a_id in activity_ids:
            old = self.activity_cost[a_id]
            new = self.calculate_cost(a_id)
            self.activity_cost[a_id] = new
            delta += (new - old)
        # cost for not using time
        empty = sum(day.count(None) for day in table)
        delta += empty * PENALTY_WEIGHTS.IDLE
        self.total_cost += delta
        return delta



# different changes
def shift_move(
            table: Table,
            activities:list[_Activity],
            atb:ATB,
            blocks:dict[int,_Block],
            day_load: list[int],
            evaluator:CostEvaluator)->ChangeResult:
    # shift a block one day before or after, and shift it by k hours (random)
    movable = [b for b in blocks.values()
                if not any(b.day == d and b.start == s and b.length == l
                for d, s, l in activities[b.activity_id].fixed_blocks)]
    if not movable:
        return ChangeResult(LIMIT.HARD,undo=lambda: None)

    block = random.choice(movable)
    activity = activities[block.activity_id]

    old_day = block.day
    old_start = block.start
    affected = {activity.id}

    day_offset = random.choice([-1,0,1])
    start_offset = random.choice([-2,-1,0,1,2])
    
    new_day = clamp(old_day+day_offset, 0,6)
    new_start = old_start+start_offset

    if new_start < activity.min_start_slot:
        return ChangeResult(LIMIT.HARD, undo=lambda: None) # maybe make the penalty scale with prio? or use the soft hard hybrid

    test_block = _Block(
        activity_id=activity.id,
        day=new_day,
        start=new_start,
        length=block.length
    )
    if not can_place(table, test_block):
        return ChangeResult(LIMIT.HARD, undo=lambda: None)

    clear_block(table,block)
    day_load[old_day]-=1
    block.day = new_day
    block.start = new_start
    place_block(table, block)
    day_load[new_day]+=1
    delta_cost = evaluator.update_activities(affected)

    delta_cost += 0.5 * activity.priority * PENALTY_WEIGHTS.PRIORITY

    def undo():
        clear_block(table, block)
        day_load[new_day] -= 1
        block.day = old_day
        block.start = old_start
        place_block(table, block)
        day_load[old_day] += 1
        evaluator.update_activities(affected)

    return ChangeResult(delta=delta_cost, undo=undo)

def swap_blocks(
            table: Table,
            activities:list[_Activity],
            atb:ATB,
            blocks:dict[int,_Block],
            day_load: list[int],
            evaluator:CostEvaluator)->ChangeResult:
    # swap two blocks of different activities
    delta_cost = 0

    b1 = random.choice(list(blocks.values()))
    b2 = random.choice(list(blocks.values()))

    if b1 == b2:
        return ChangeResult(LIMIT.HARD, undo=lambda: None)

    a1 = activities[b1.activity_id]
    a2 = activities[b2.activity_id]

    if any((b1.day, b1.start, b1.length)==fixed for fixed in a1.fixed_blocks):
        return ChangeResult(LIMIT.HARD, undo=lambda: None)
    if any((b2.day, b2.start, b2.length)==fixed for fixed in a2.fixed_blocks):
        return ChangeResult(LIMIT.HARD, undo=lambda: None)
    
    old1 = (b1.day, b1.start)
    old2 = (b2.day, b2.start)
    affected = {a1.id, a2.id}

    test1 = _Block(id=b1.id, activity_id=b2.activity_id, day=b2.day, start=b2.start, length=b1.length)
    test2 = _Block(id=b2.id, activity_id=b1.activity_id, day=b1.day, start=b1.start, length=b2.length)

    if not (can_place(table, test1) and can_place(table, test2)):
        return ChangeResult(LIMIT.HARD, undo=lambda: None)

    clear_block(table, b1)
    clear_block(table, b2)

    day_load[b1.day] -= 1
    day_load[b2.day] -= 1

    b1.day, b1.start = b2.day, b2.start
    b2.day, b2.start = old1

    place_block(table, b1)
    place_block(table, b2)

    day_load[b1.day] += 1
    day_load[b2.day] += 1

    delta_cost = evaluator.update_activities(affected)

    def undo():

        clear_block(table, b1)
        clear_block(table, b2)

        day_load[b1.day] -= 1
        day_load[b2.day] -= 1

        b1.day, b1.start = old1
        b2.day, b2.start = old2

        place_block(table, b1)
        place_block(table, b2)

        day_load[b1.day] += 1
        day_load[b2.day] += 1

        evaluator.update_activities(affected)


    return ChangeResult(delta_cost, undo=undo)

def resize_block(
            table: Table,
            activities:list[_Activity],
            atb:ATB,
            blocks:dict[int,_Block],
            day_load: list[int],
            evaluator:CostEvaluator)->ChangeResult:
    # change the length of a block by 1 slot

    movable = [b for b in blocks.values()
                if not any(b.day == d and b.start == s and b.length == l
                for d, s, l in activities[b.activity_id].fixed_blocks)]
    if not movable:
        return ChangeResult(LIMIT.HARD, undo=lambda: None)

    block = random.choice(movable)
    activity = activities[block.activity_id]

    old_length = block.length
    affected = {activity.id}

    direction = random.choice([-1,1])

    if direction == -1:
        if block.length == 1:
            return ChangeResult(LIMIT.HARD, undo=lambda: None)
        clear_block(table,block)
        block.length -= 1
        place_block(table, block)
        delta_cost = evaluator.update_activities(affected)
        return ChangeResult(delta_cost, undo=lambda: None)

    if block.length + 1 > activity.max_block_slots:
        return ChangeResult(LIMIT.SOFT, undo=lambda: None)

    next_slot = block.start + block.length
    if next_slot >= SLOTS_PER_DAY:
        return ChangeResult(LIMIT.HARD, undo=lambda: None)
    if table[block.day][next_slot] is not None:
        return ChangeResult(LIMIT.HARD, undo=lambda: None)

    clear_block(table,block)
    block.length += 1
    place_block(table, block)
    delta_cost = evaluator.update_activities(affected)

    def undo():
        clear_block(table, block)
        block.length = old_length
        place_block(table, block)
        evaluator.update_activities(affected)
    
    return ChangeResult(delta=delta_cost, undo=undo)

def split_block(
            table: Table,
            activities:list[_Activity],
            atb:ATB,
            blocks:dict[int,_Block],
            day_load: list[int],
            evaluator:CostEvaluator)->ChangeResult:
    # if length>max length, split block
    delta_cost = 0
    return ChangeResult(LIMIT.HARD, undo=lambda: None)

def random_reschedule(
            table: Table,
            activities:list[_Activity],
            atb:ATB,
            blocks:dict[int,_Block],
            day_load: list[int],
            evaluator:CostEvaluator,
            scheduler:Callable,
            max_priority_allowed:int=5)->ChangeResult:
    # completely delete an activity's blocks and re-insert using greedy (lowest priority)
    low_prio_activities = [a for a in activities
                        if a.priority <= max_priority_allowed]
    if not low_prio_activities:
        return ChangeResult(LIMIT.HARD, undo=lambda: None)

    activity = random.choice(low_prio_activities)


    removed: list[tuple[int, _Block]] = []
    for block_id in list(atb[activity.id]):
        b = blocks[block_id]
        removed.append((block_id, block))
        clear_block(table, b)
        day_load[b.day] -= 1
        del blocks[block_id]
    atb[activity.id].clear()

    old_cost = evaluator.activity_cost[activity.id]
    
    scheduler(activity, table, blocks, atb, day_load)

    new_cost = evaluator.calculate_cost(activity.id)
    evaluator.activity_cost[activity.id] = new_cost
    delta_cost = new_cost - old_cost
    evaluator.total_cost += delta_cost

    def undo():
        for block_id in list(atb[activity.id]):
            block = blocks[block_id]
            clear_block(table, block)
            day_load[block.day]-=1
            del blocks[block_id]
        atb[activity.id].clear()

        for block_id, block in removed:
            place_block(table, block)
            blocks[block_id] = block
            atb[activity.id].add(block_id)

        evaluator.activity_cost[activity.id] = old_cost
        evaluator.total_cost -= delta_cost

    return ChangeResult(delta_cost, undo=undo)

class Annealer:

    def __init__(self,
                table: Table,
                activities:list[_Activity],
                atb:ATB,
                blocks:dict[int,_Block],
                day_load: list[int],
                scheduler:Callable[[ _Activity, Table,
                                            dict[int, _Block],
                                            ATB,
                                            list[int]], None],
                ) -> None:
        self.activities = {a.id: a for a in activities}
        self.scheduler = scheduler
        
        self.table = table
        self.blocks = blocks
        self.atb = atb
        self.day_load = day_load

        self.evaluator = CostEvaluator(self.activities,
                                    self.blocks,
                                    self.atb,
                                    self.day_load
                                    )

        self.T = 1e6
        self.T_MIN = 1e-4
        self.cooling = 0.95
        self.cycles = 1000

        self.change_factories = [
            lambda: shift_move(self.table, activities, self.atb,
                            self.blocks, self.day_load, self.evaluator),
            lambda: resize_block(self.table, activities, self.atb,
                                self.blocks, self.day_load, self.evaluator),
            lambda: swap_blocks(self.table, activities, self.atb,
                            self.blocks, self.day_load, self.evaluator),
        ]
        _ =[
            lambda: random_reschedule(self.table, activities, self.atb,
                                        self.blocks, self.day_load, self.evaluator,
                                        self.scheduler, max_priority_allowed=5)
        ]

    def run(self):
        current_cost = self.evaluator.total_cost
        best_cost = current_cost
        best_table = copy.deepcopy(self.table)
        best_blocks = copy.deepcopy(self.blocks)

        T = self.T

        while T > self.T_MIN:
            for _ in range(self.cycles):
                change = random.choice(self.change_factories)()
                delta_cost = change.delta

                if delta_cost <= 0 or (random.random() < math.exp(-delta_cost/T)):
                    current_cost += delta_cost
                    #print(f'Accepted d={round(delta_cost,3)!s:6s}  current cost={round(current_cost,3)!s:6s}')
                    if current_cost < best_cost:
                        best_cost = current_cost
                        best_table = copy.deepcopy(self.table)
                        best_blocks = copy.deepcopy(self.blocks)
                        #print(f'Updating cost: {round(best_cost,3)!s:6s}')
                else:
                    change.undo()
            T *= self.cooling

        return best_table, best_blocks, best_cost



if __name__ == "__main__":
    # ai -generated activities
    activities = [
    # ------------------------------------------------------------------
    # 0 – Full‑time work (fixed 9 am‑5 pm Mon‑Fri, highest priority)
    # ------------------------------------------------------------------
    _Activity(
        name='Work',
        frequency=5,                    # one block per weekday
        even_spacing=False,
        min_weekly_minutes=2400,        # 40 h = 2400 min
        max_block_minutes=480,          # 8 h per block (480 min)
        min_start_minutes=9*60,         # 09:00 (irrelevant – already fixed)
        fixed=[                         # (day, start_min, length_min)
            (0, 9*60, 480),   # Monday
            (1, 9*60, 480),   # Tuesday
            (2, 9*60, 480),   # Wednesday
            (3, 9*60, 480),   # Thursday
            (4, 9*60, 480),   # Friday
        ],
        priority=5,
    ),

    # ------------------------------------------------------------------
    # 1 – Study (evenly spaced, night‑time, 3 × / week, priority 2)
    # ------------------------------------------------------------------
    _Activity(
        name='Study',
        frequency=3,
        even_spacing=True,
        min_weekly_minutes=240,         # 4 h total
        max_block_minutes=120,           # at most 2 h per session
        min_start_minutes=20*60,        # cannot start before 20:00
        fixed=[],
        priority=4,
    ),

    # ------------------------------------------------------------------
    # 2 – Piano lesson (fixed Thursday 18:00‑19:00, low priority)
    # ------------------------------------------------------------------
    _Activity(
        name='Piano',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=60,
        max_block_minutes=60,
        min_start_minutes=0,           # not used – fixed overrides it
        fixed=[(3, 18*60, 60)],         # Thursday 18:00‑19:00
        priority=3,
    ),

    # ------------------------------------------------------------------
    # 3 – Exercise (early‑morning, 2 × / week, priority 1)
    # ------------------------------------------------------------------
    _Activity(
        name='Exercise',
        frequency=2,
        even_spacing=False,
        min_weekly_minutes=120,         # 2 h total
        max_block_minutes=60,           # at most 1 h per session
        min_start_minutes=5*60,         # cannot start before 05:00
        fixed=[],
        priority=4,
    ),

    # ------------------------------------------------------------------
    # 4 – Yoga (morning, evenly spaced, 2 × / week, priority 2)
    # ------------------------------------------------------------------
    _Activity(
        name='Yoga',
        frequency=2,
        even_spacing=True,
        min_weekly_minutes=90,          # 1.5 h total
        max_block_minutes=60,           # ≤ 1 h per session
        min_start_minutes=6*60,        # cannot start before 06:00
        fixed=[],
        priority=3,
    ),

    # ------------------------------------------------------------------
    # 5 – Cooking (evenings, 3 × / week, priority 3)
    # ------------------------------------------------------------------
    _Activity(
        name='Cooking',
        frequency=3,
        even_spacing=False,
        min_weekly_minutes=180,         # 3 h total
        max_block_minutes=120,          # can be a 2‑hour dinner prep
        min_start_minutes=17*60,        # cannot start before 17:00
        fixed=[],
        priority=2,
    ),

    # ------------------------------------------------------------------
    # 6 – Grocery shopping (once a week, midday, priority 4)
    # ------------------------------------------------------------------
    _Activity(
        name='Groceries',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=60,
        max_block_minutes=60,
        min_start_minutes=10*60,        # cannot start before 10:00
        fixed=[],
        priority=2,
    ),

    # ------------------------------------------------------------------
    # 7 – Cleaning (once a week, morning, priority 4)
    # ------------------------------------------------------------------
    _Activity(
        name='Cleaning',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=120,
        max_block_minutes=120,
        min_start_minutes=9*60,
        fixed=[],
        priority=1,
    ),

    # ------------------------------------------------------------------
    # 8 – Laundry (once a week, early‑morning, priority 4)
    # ------------------------------------------------------------------
    _Activity(
        name='Laundry',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=60,
        max_block_minutes=60,
        min_start_minutes=9*60,
        fixed=[],
        priority=2,
    ),

    # ------------------------------------------------------------------
    # 9 – Reading (evenly spaced, night, 3 × / week, low priority)
    # ------------------------------------------------------------------
    _Activity(
        name='Reading',
        frequency=3,
        even_spacing=True,
        min_weekly_minutes=180,         # 3 h total
        max_block_minutes=90,           # at most 1.5 h per session
        min_start_minutes=20*60,        # cannot start before 20:00
        fixed=[],
        priority=1,
    ),

    # ------------------------------------------------------------------
    # 10 – Spanish (language learning, 2 × / week, evening, priority 5)
    # ------------------------------------------------------------------
    _Activity(
        name='Spanish',
        frequency=2,
        even_spacing=True,
        min_weekly_minutes=120,         # 2 h total
        max_block_minutes=60,           # ≤ 1 h per session
        min_start_minutes=19*60,        # cannot start before 19:00
        fixed=[],
        priority=1,
    ),


    # ------------------------------------------------------------------
    # 12 – Volunteer (once a week, mid‑morning, priority 2)
    # ------------------------------------------------------------------
    _Activity(
        name='Volunteer',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=180,          # 3 h total
        max_block_minutes=180,
        min_start_minutes=9*60,          # cannot start before 09:00
        fixed=[],
        priority=3,
    ),

    # ------------------------------------------------------------------
    # 13 – Meditation (short, 3 × / week, priority 5)
    # ------------------------------------------------------------------
    _Activity(
        name='Meditation',
        frequency=3,
        even_spacing=False,
        min_weekly_minutes=30,           # 30 min total
        max_block_minutes=30,            # each block ≤ 30 min
        min_start_minutes=6*60,          # cannot start before 06:00
        fixed=[],
        priority=1,
    ),

    # ------------------------------------------------------------------
    # 14 – Hiking (weekend‑only, long block, priority 3)
    # ------------------------------------------------------------------
    _Activity(
        name='Hiking',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=240,          # 4 h total
        max_block_minutes=240,           # can be a single 4‑hour block
        min_start_minutes=8*60,          # cannot start before 08:00
        fixed=[(5, 8*60, 240)],           # Saturday 08:00‑12:00
        priority=3,
    ),

    # ------------------------------------------------------------------
    # 15 – MealPrep (3 × / week, evening, priority 4)
    # ------------------------------------------------------------------
    _Activity(
        name='MealPrep',
        frequency=3,
        even_spacing=False,
        min_weekly_minutes=180,          # 3 h total
        max_block_minutes=60,            # each meal prep ≤ 1 h
        min_start_minutes=17*60,         # cannot start before 17:00
        fixed=[],
        priority=2,
    ),

    # ------------------------------------------------------------------
    # 16 – Homework (2 × / week, night, priority 2)
    # ------------------------------------------------------------------
    _Activity(
        name='Homework',
        frequency=2,
        even_spacing=False,
        min_weekly_minutes=120,          # 2 h total
        max_block_minutes=90,            # ≤ 1.5 h per session
        min_start_minutes=19*60,        # cannot start before 19:00
        fixed=[],
        priority=2,
    ),

    # ------------------------------------------------------------------
    # 17 – Language exchange (fixed Wednesday 20:00‑21:30, priority 3)
    # ------------------------------------------------------------------
    _Activity(
        name='LangExchange',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=90,
        max_block_minutes=90,
        min_start_minutes=0,
        fixed=[(2, 20*60, 90)],           # Wednesday 20:00‑21:30
        priority=2,
    ),

    # ------------------------------------------------------------------
    # 18 – Family time (2 × / week, evening, priority 2)
    # ------------------------------------------------------------------
    _Activity(
        name='FamilyTime',
        frequency=2,
        even_spacing=False,
        min_weekly_minutes=180,          # 3 h total
        max_block_minutes=120,           # ≤ 2 h per session
        min_start_minutes=18*60,        # cannot start before 18:00
        fixed=[],
        priority=3,
    ),

    # ------------------------------------------------------------------
    # 19 – Relax (optional low‑priority filler, 1 × / week, any time)
    # ------------------------------------------------------------------
    _Activity(
        name='Relax',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=60,           # just a half‑hour somewhere
        max_block_minutes=120,
        min_start_minutes=0,
        fixed=[],
        priority=1,                      # lowest priority – the algorithm will move it freely
    ),
]


    blocks, table, activity_to_blocks, day_load = greedy_initial(activities)



    evaluator = CostEvaluator(
        activities={a.id:a for a in activities},
        blocks=blocks,
        atb=activity_to_blocks,
        day_load=day_load
        )

    initial_cost = evaluator.total_cost
    
    annealer = Annealer(
        table=table,
        activities=activities,
        blocks=blocks,
        atb=activity_to_blocks,
        day_load=day_load,
        scheduler=schedule_activity
    )

    best_table, best_blocks, best_cost = annealer.run()

    print('\n\nRESULTS =======================================')

    for day in range(SCHEDULE_SIZE):
        print(f'----- day {day}-------------------')
        day_blocks = [b for b in blocks.values() if b.day == day]
        day_blocks.sort(key=lambda b: b.start)

        for block in day_blocks:
            activity = next(a for a in activities if a.id == block.activity_id)
            start_mins = block.start * SLOT_SIZE
            end_mins = (block.start + block.length) * SLOT_SIZE
            start_hours = start_mins // 60
            start_mins = start_mins % 60
            end_hours = end_mins // 60
            end_mins = end_mins % 60
            print(
                f"  {activity.name:12s}  [{block.id:02d}]  "
                f"{start_hours:02d}:{start_mins:02d} - {end_hours:02d}:{end_mins:02d}  "
                f"(len={block.length} slots)"
            )

    print('\n\nOptimised =======================================')


    for day in range(SCHEDULE_SIZE):
        print(f'----- day {day}-------------------')
        day_blocks = [b for b in best_blocks.values() if b.day == day]
        day_blocks.sort(key=lambda b: b.start)

        for block in day_blocks:
            activity = next(a for a in activities if a.id == block.activity_id)
            start_mins = block.start * SLOT_SIZE
            end_mins = (block.start + block.length) * SLOT_SIZE
            start_hours = start_mins // 60
            start_mins = start_mins % 60
            end_hours = end_mins // 60
            end_mins = end_mins % 60
            print(
                f"  {activity.name:12s}  [{block.id:02d}]  "
                f"{start_hours:02d}:{start_mins:02d} - {end_hours:02d}:{end_mins:02d}  "
                f"(len={block.length} slots)"
            )

    print('INFO ====================================')
    print(f'Init Cost:  {initial_cost:.2f}')
    print(f'Final Cost: {best_cost:.2f}')