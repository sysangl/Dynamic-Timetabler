import collections
import copy
import math
import random
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

# from  import Block

type ATB = dict[int, set[int]]
type Table = list[list[int | None]]


@dataclass
class ChangeResult:
    delta: float
    undo: Callable
    mark_undo: bool = False

class LIMIT:
    HARD = math.inf
    HARD_SOFT = 10.0
    SOFT = 10.0
    NORMAL = 1.0

class PENALTY_WEIGHTS:
    MIN_TIME = 1.0
    FREQ = 2.0
    EVEN_SPACING = 5.0
    OVERLOAD = 3.0
    PRIORITY = 3.0
    IDLE = 3.0
    BALANCE = 20.0
    FRAGMENT = 8.0
    EARLY_BOUND = 40.0
    LATE_BOUND = 60.0


# parameters
# DAYS = 7


MAX_PRIORITY = 10
#penalty modifs

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
        try:
            if slot >= _Schedule.SLOTS_PER_DAY or not (0<=b.day<_Schedule.SIZE):
                return False
            if table[b.day][slot] not in {None, b.id}:
                return False
        except IndexError:
            print(f'can_place failed : slot {slot}')
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
        target_days = [min(max(0, round(i * _Schedule.SIZE / needed_sessions)), _Schedule.SIZE-1) for i in range(needed_sessions)]
    else:
        target_days = [None] * needed_sessions

    for idx, block_length in enumerate(lengths):
        candidate_days: list[int] = []
        if activity.even_spacing:
            ideal = target_days[idx]
            offsets = []
            for day in range(_Schedule.SIZE):
                offsets.append(day)
                offsets.append(-day)
            for offset in offsets:
                day = ideal + offset
                if 0<=day<_Schedule.SIZE and day not in used_days:
                    candidate_days.append(day)
            if not candidate_days:
                candidate_days = list(range(_Schedule.SIZE))

        else:
            activities_per_day = [
                (day, sum(1 for id in activity_to_blocks[activity.id] if blocks[id].day == day), day_load[day]) for day in range(_Schedule.SIZE)
            ]
            activities_per_day.sort(key=lambda x: (x[1],x[2]))
            candidate_days = [day for day,_,_ in activities_per_day]

        placed = False

        slot_variation = random.randint(-120//_Schedule.SLOT_SIZE, 120//_Schedule.SLOT_SIZE,)

        for day in candidate_days:
            free_slots_start = find_free_slots(day, block_length, table, start_from=clamp(activity.min_start_slot+slot_variation, 0, 24))
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
                    free_slots_start = find_free_slots(day, reduced_length, table, start_from=activity.min_start_slot+slot_variation)
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

def greedy_initial(activities: list[_Activity], schedule_size:int=_Schedule.SIZE, slots_per_day:int=_Schedule.SLOTS_PER_DAY, slot_size:int=_Schedule.SLOT_SIZE):
    table: Table = [[None for _ in range(slots_per_day) ] for _ in range(_Schedule.SIZE)]
    blocks: dict[int, _Block] = {}
    activity_to_blocks:ATB = {}
    activity_to_blocks = {a.id: set() for a in activities}
    day_load:list[int] = [0]*slot_size

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
                day_load: list[int],
                table:Table,
                ) -> None:

        self.activities = activities
        self.blocks = blocks
        self.atb = atb
        self.day_load = day_load
        self.activity_cost = {a_id: self.calculate_cost(a_id) for a_id in self.activities}
        self.total_cost = sum(self.activity_cost.values())
        self.idle = 0
        self.table = table

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
            ideal = _Schedule.SIZE / activity.frequency
            # calcultaing standard error, spesh coming in clutch
            standard_err = sum((days[day+1]-days[day]-ideal) for day in range(len(days)-1))
            cost += standard_err**2 * PENALTY_WEIGHTS.EVEN_SPACING

        #cost for over load
        blocks_per_day = collections.Counter(b.day for b in block_list)
        target = math.ceil(activity.frequency/_Schedule.SIZE)
        for count in blocks_per_day.values():
            if count > target:
                cost += (count-target)**2 * PENALTY_WEIGHTS.OVERLOAD

        #cost for block size
        for b in block_list:
            if b.length > activity.max_block_slots:
                cost+= LIMIT.HARD_SOFT * 2

            early_oob = sum(1 for slot in range(b.start, b.start + b.length) if _Schedule.EARLY_SLOTS > slot)
            late_oob = sum(1 for slot in range(b.start, b.start + b.length) if _Schedule.LATE_SLOTS < slot)
            cost += early_oob**2 * PENALTY_WEIGHTS.EARLY_BOUND + late_oob**2 * PENALTY_WEIGHTS.LATE_BOUND

            if b.start < activity.min_start_slot:
                cost += (b.start-activity.min_start_slot)**2

        # fragmentation (minimise # of blocks)
        if len(block_list) > activity.frequency:
            cost += (len(block_list)-activity.frequency) * PENALTY_WEIGHTS.FRAGMENT

        #scale w/ prio
        return cost * activity.priority

    def _idle_penalty(self):
        # cost for not using time
        empty = sum(day.count(None) for day in self.table)
        idle_prev = self.idle
        idle_current = empty * PENALTY_WEIGHTS.IDLE
        self.idle = idle_current
        return idle_current - idle_prev 

    def update_activities(self, activity_ids):
        delta = 0
        for a_id in activity_ids:
            old = self.activity_cost[a_id]
            new = self.calculate_cost(a_id)
            self.activity_cost[a_id] = new
            delta += (new - old)

        ## whole table penalties
        delta += self._idle_penalty()

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
    new_start = clamp(old_start+start_offset, 0, 23)

    # if new_start < activity.min_start_slot:
    #     return ChangeResult(LIMIT.HARD, undo=lambda: None) # maybe make the penalty scale with prio? or use the soft hard hybrid

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
    if next_slot >= _Schedule.SLOTS_PER_DAY:
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
    
    oversized = [b for b in blocks.values() if b.length > activities[b.activity_id].max_block_slots]

    if not oversized:
        return ChangeResult(LIMIT.HARD, undo=lambda: None)

    parent = random.choice(oversized)
    activity = activities[parent.activity_id]

    parent_copy = _Block(
        id=parent.id,
        activity_id=parent.activity_id,
        day=parent.day,
        start=parent.start,
        length=parent.length
    )

    split_point = random.randint(1,parent.length-1)

    child1 = _Block(activity_id=parent.activity_id, day=parent.day, start=parent.start, length=split_point)
    child2 = _Block(activity_id=parent.activity_id, day=parent.day, start=parent.start+split_point, length=parent.length-split_point)

    clear_block(table, parent)
    day_load[parent.day] -= 1

    # check placement
    # restore
    if not (can_place(table, child1) and can_place(table, child2)):
        place_block(table, parent)
        day_load[parent.day] += 1
        return ChangeResult(delta=LIMIT.HARD, undo=lambda: None)

    place_block(table, child1)
    place_block(table, child2)

    del blocks[parent.id]
    blocks[child1.id] = child1
    blocks[child2.id] = child2
    atb[activity.id].remove(parent.id)
    atb[activity.id].update({child1.id, child2.id})
    day_load[parent.day] += 2

    delta_cost = evaluator.update_activities({activity.id})

    def undo():
        clear_block(table, child1)
        clear_block(table, child2)
        day_load[parent.day] -= 2
        del blocks[child1.id]
        del blocks[child2.id]
        atb[activity.id].remove(child1.id)
        atb[activity.id].remove(child2.id)

        place_block(table, parent_copy)
        blocks[parent_copy.id] = parent_copy
        atb[activity.id].add(parent_copy.id)
        day_load[parent.day] += 1

        evaluator.update_activities({activity.id})

    return ChangeResult(delta_cost, undo=undo)


def merge_blocks(
            table: Table,
            activities:list[_Activity],
            atb:ATB,
            blocks:dict[int,_Block],
            day_load: list[int],
            evaluator:CostEvaluator)->ChangeResult:

    candidates: list[tuple[_Activity, _Block, _Block]] = []

    for a in activities:
        blocks_in_day:dict[int, list[_Block]] = {}
        for bid in atb[a.id]:
            b = blocks[bid]
            blocks_in_day.setdefault(b.day, []).append(b)

        for block_list in blocks_in_day.values():
            block_list.sort(key=lambda b: b.start)
            for i in range(len(block_list)-1):
                b1, b2 = block_list[i], block_list[i+1]

                if b1.start + b1.length == b2.start:
                    candidates.append((a, b1, b2))

    if not candidates:
        return ChangeResult(LIMIT.HARD, undo=lambda: None)

    activity, b1, b2 = random.choice(candidates)

    old_b1 = _Block(
                    id=b1.id,
                    activity_id=b1.activity_id,
                    day=b1.day,
                    start=b1.start,
                    length=b1.length
                    )

    old_b2 = _Block(
                    id=b2.id,
                    activity_id=b2.activity_id,
                    day=b2.day,
                    start=b2.start,
                    length=b2.length
                    )

    clear_block(table, b1)
    clear_block(table, b2)
    day_load[b1.day] -= 2

    merged_start = b1.start
    merged_length = b1.length + b2.length
    b1.start = merged_start
    b1.length = merged_length
    place_block(table, b1)
    day_load[b1.day] += 1

    del blocks[b2.id]
    atb[activity.id].remove(b2.id)

    affected={activity.id}

    delta_cost = evaluator.update_activities(affected)


    def undo():
        clear_block(table, b1)
        day_load[b1.day] -= 1

        b1.start = old_b1.start
        b1.length = old_b1.length
        b2.start = old_b2.start
        b2.length = old_b2.length

        place_block(table, b1)
        place_block(table, b2)

        day_load[b1.day] += 2
        blocks[b2.id] = b2
        atb[activity.id].add(b2.id)

        evaluator.update_activities(affected)

    return ChangeResult(delta_cost, undo=undo)


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

    try:
        scheduler(activity, table, blocks, atb, day_load)
    except RuntimeError:
        delta_cost = LIMIT.HARD

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

    return ChangeResult(delta_cost, undo=undo,mark_undo=delta_cost==LIMIT.HARD)

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
                                    self.day_load,
                                    self.table
                                    )

        self.T = 1e9
        self.T_MIN = 1e-6
        self.cooling = 0.85
        self.cycles = 100000

        self.change_factories = [
            lambda: shift_move(self.table, activities, self.atb,
                            self.blocks, self.day_load, self.evaluator),
            lambda: resize_block(self.table, activities, self.atb,
                                self.blocks, self.day_load, self.evaluator),
            lambda: swap_blocks(self.table, activities, self.atb,
                            self.blocks, self.day_load, self.evaluator),
        ]
        _=[
            lambda: random_reschedule(self.table, activities, self.atb,
                                        self.blocks, self.day_load, self.evaluator,
                                        self.scheduler, max_priority_allowed=5)
        ]

    def run(self):
        cost_updates = 0
        accept_counter = 0
        undo_counter = 0
        best_cost = self.evaluator.total_cost
        best_table = copy.deepcopy(self.table)
        best_blocks = copy.deepcopy(self.blocks)

        T = self.T

        while T > self.T_MIN:
            for _ in range(self.cycles):
                change = random.choice(self.change_factories)()
                if change.mark_undo:
                    change.undo()
                    undo_counter += 1
                    continue
    
                delta_cost = change.delta

                if delta_cost <= 0 or (random.random() < math.exp(-delta_cost/T)):
                    accept_counter += 1
                    if self.evaluator.total_cost < best_cost:
                        best_cost = self.evaluator.total_cost
                        best_table = copy.deepcopy(self.table)
                        best_blocks = copy.deepcopy(self.blocks)
                        sys.stdout.write(f'\r[{cost_updates!s:8s}] Updating cost: {best_cost}')
                        sys.stdout.flush()
                        cost_updates += 1
                else:
                    undo_counter += 1
                    change.undo()
            T *= self.cooling

        print('\n Post Anneal Run Stats')
        print(f'Cost Updates   : {cost_updates}')
        print(f'Accept Counter : {accept_counter}')
        print(f'Undo Counter   : {undo_counter}')
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
        frequency=7,
        even_spacing=True,
        min_weekly_minutes=720,         # 4 h total
        max_block_minutes=120,           # at most 2 h per session
        min_start_minutes=17*60,        # cannot start before 20:00
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
        min_weekly_minutes=240,         # 2 h total
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
        frequency=7,
        even_spacing=True,
        min_weekly_minutes=80,           # 30 min total
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
        frequency=2,
        even_spacing=False,
        min_weekly_minutes=360,          # 4 h total
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
        frequency=6,
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
        frequency=5,
        even_spacing=False,
        min_weekly_minutes=260,          # 2 h total
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

    schedule = _Schedule()

    blocks, table, activity_to_blocks, day_load = greedy_initial(activities)





    
    annealer = Annealer(
        table=table,
        activities=activities,
        blocks=blocks,
        atb=activity_to_blocks,
        day_load=day_load,
        scheduler=schedule_activity
    )

    initial_cost = annealer.evaluator.total_cost
    print(initial_cost)

    print('\n\nRESULTS =======================================')
    print('\n\nINITIAL =======================================')
    for day in range(_Schedule.SIZE):
        print(f'----- day {day}-------------------')
        day_blocks = [b for b in blocks.values() if b.day == day]
        day_blocks.sort(key=lambda b: b.start)

        for block in day_blocks:
            activity = next(a for a in activities if a.id == block.activity_id)
            start_mins = block.start * _Schedule.SLOT_SIZE
            end_mins = (block.start + block.length) * _Schedule.SLOT_SIZE
            start_hours = start_mins // 60
            start_mins = start_mins % 60
            end_hours = end_mins // 60
            end_mins = end_mins % 60
            print(
                f"  {activity.name:12s}  [{block.id:02d}]  "
                f"{start_hours:02d}:{start_mins:02d} - {end_hours:02d}:{end_mins:02d}  "
                f"(len={block.length} slots)"
            )

    print('\n\nOptimised ======================================')

    best_table, best_blocks, best_cost = annealer.run()

    for day in range(_Schedule.SIZE):
        print(f'----- day {day}-------------------')
        day_blocks = [b for b in best_blocks.values() if b.day == day]
        day_blocks.sort(key=lambda b: b.start)

        for block in day_blocks:
            activity = next(a for a in activities if a.id == block.activity_id)
            start_mins = block.start * _Schedule.SLOT_SIZE
            end_mins = (block.start + block.length) * _Schedule.SLOT_SIZE
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
    print(f'Init Cost:  {initial_cost}')
    print(f'Final Cost: {best_cost}')