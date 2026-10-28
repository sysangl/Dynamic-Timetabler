import collections
import copy
import math
import random

# from  import Block

type ATB = dict[int, set[int]]
type Table = list[list[int | None]]

# parameters
# DAYS = 7
SCHEDULE_SIZE = 7
MINS_IN_DAY = 24 * 60
SLOT_SIZE = 30 #mins
SLOTS_PER_DAY = MINS_IN_DAY//SLOT_SIZE

T_0 = 1e6
T_MIN = 1e-5 # need to tweak to find optimal
CYCLES_PER_T = 1000
C_F = 0.95 # cooling factor

MAX_PRIORITY = 10
#penalty modifs
class LIMIT:
    HARD = math.inf
    HARD_SOFT = 100.0
    SOFT = 10.0
    NORMAL = 1.0

class PENALTY_WEIGHTS:
    MIN_TIME = 1.0
    FREQ = 2.0
    EVEN_SPACING = 2.0
    OVERLOAD = 3.0
    PRIORITY = 3.0

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
                length:int
                ) -> None:
        self.id:int = self.generate_id()
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
    return min(max_value,max(min_value,0))

def clear_block(table:Table ,b:_Block):
    for slot in range(b.start, b.start + b.length):
        table[b.day][slot] = 0

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
    return table

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

# 
# simultaed annealing
# 
class Annealer:
    class CostEvaluator:
        def __init__(self,
                    activities: dict[int,_Activity],
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
                cost += standard_err * PENALTY_WEIGHTS.EVEN_SPACING

            #cost for over load
            blocks_per_day = collections.Counter(b.day for b in block_list)
            target = math.ceil(activity.frequency/SCHEDULE_SIZE)
            for count in blocks_per_day.values():
                if count > target:
                    cost += (count-target) * PENALTY_WEIGHTS.OVERLOAD

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
            self.total_cost += delta
            return delta


    def __init__(self,
                table:Table,
                activities: list[_Activity],
                blocks: dict[int, _Block],
                atb: ATB,
                day_load: list[int]
                ) -> None:
        self.activities = {a.id: a for a in activities}
        self.blocks=blocks
        self.atb=atb
        self.day_load=day_load
        self.table: Table = table
        self.saved_table:Table = self.table
        self.saved_state:tuple[Table, dict[int, _Block],ATB, list[int]] = (table, blocks, atb, day_load)

        self.evaluator = self.CostEvaluator(
            activities=self.activities,
            blocks=self.blocks,
            atb=self.atb,
            day_load=self.day_load
            )

    def cool(self, T):
        return T*C_F

    # different changes
    def shift_move(self)->float:
        # shift a block one day before or after, and shift it by k hours (random)
        movable = [b for b in blocks.values()
                    if not any(b.day == d and b.start == s and b.length == l
                    for d, s, l in activities[b.activity_id].fixed_blocks)]
        if not movable:
            return LIMIT.HARD

        block = random.choice(movable)
        activity = activities[block.activity_id]

        old_day = block.day
        old_start = block.start
        affected = {activity.id}

        day_offset = random.choice([-1,0,1])
        start_offset = random.choice([-2,-1,0,1,2])
        
        new_day = clamp(old_day+day_offset, 0,7)
        new_start = old_start+start_offset

        if new_start < activity.min_start_slot:
            return LIMIT.HARD # maybe make the penalty scale with prio? or use the soft hard hybrid

        test_block = _Block(
            activity_id=activity.id,
            day=new_day,
            start=new_start,
            length=block.length
        )
        if not can_place(self.table, test_block):
            return LIMIT.HARD

        clear_block(self.table,block)
        self.day_load[old_day]-=1
        block.day = new_day
        block.start = new_start
        place_block(table, block)
        self.day_load[new_day]+=1
        delta_cost = self.evaluator.update_activities(affected)

        delta_cost += activity.priority * PENALTY_WEIGHTS.PRIORITY

        return delta_cost

    def resize_block(self, table: Table)->float:
        # change the length of a block by 1 slot
        delta_cost = 0
        return delta_cost

    def swap_blocks(self, table:Table)->float:
        # swap two blocks of different activities
        delta_cost = 0
        return delta_cost

    def split_move(self, table: Table)->float:
        # if length>max length, split block
        delta_cost = 0
        return delta_cost

    def random_reschedule(self, table:Table)->float:
        # completely delete an activity's blocks and re-insert using greedy (lowest priority)
        delta_cost = 0
        return delta_cost


    def propose_change(self)->float:
        #change_type = random.choice(['shift', 'resize', 'swap', 'split', 'random'])
        change_type = 'shift'
        match change_type:
            case 'shift':
                return self.shift_move()
            case 'resize':
                return self.resize_block(table)
            case 'swap':
                return self.swap_blocks(table)
            case 'split':
                return self.split_move(table)
            case 'random':
                return self.random_reschedule(table)
        return math.inf

    def save_state(self, table:Table, block:dict[int, _Block], atb:ATB, day_load:list[int]):
        self.saved_state = (table, block,atb,day_load)

    def revert_change(self):
        self.table, self.blocks, self.atb, self.day_load = self.saved_state

    def simulate_annealing(self, table:Table):
        T = T_0
        current_cost = self.evaluator.total_cost
        best_table = copy.deepcopy(table)
        best_blocks = copy.deepcopy(self.blocks)
        best_cost = current_cost
        saved_table = copy.deepcopy(table)

        while T > T_MIN:
            for _ in range(CYCLES_PER_T):
                saved_table = copy.deepcopy(table)
                delta_cost = self.propose_change()
                if delta_cost <= 0 or random.random() < math.exp(-delta_cost/T):
                    current_cost += delta_cost
                    if current_cost < best_cost:
                        best_cost = current_cost
                        best_table = copy.deepcopy(table)
                        print(f'Updating cost: {current_cost} -> {best_cost}')
                else:
                    table = saved_table
            T = self.cool(T)

        return best_table, best_blocks, best_cost



if __name__ == "__main__":
    # ai -generated activities
    activities = [
        # ------------------------------------------------------------------
        #  0 – Full‑time work (fixed 9 am‑5 pm Mon‑Fri)
        # ------------------------------------------------------------------
        _Activity(
            name='Work',
            frequency=5,                     # Mon‑Fri
            even_spacing=False,
            min_weekly_minutes=2400,          # 40 h / week
            max_block_minutes=480,           # 8 h per day
            min_start_minutes=9*60,          # 09:00 (irrelevant – already fixed)
            fixed=[
                (0, 9*60, 480),   # Monday
                (1, 9*60, 480),   # Tuesday
                (2, 9*60, 480),   # Wednesday
                (3, 9*60, 480),   # Thursday
                (4, 9*60, 480),   # Friday
            ],
            priority=1,
        ),

        # ------------------------------------------------------------------
        #  1 – Study (evenly spaced, night‑time, 3×/week)
        # ------------------------------------------------------------------
        _Activity(
            name='Study',
            frequency=3,
            even_spacing=True,
            min_weekly_minutes=240,
            max_block_minutes=120,
            min_start_minutes=20*60,        # cannot start before 20:00
            fixed=[],
            priority=2,
        ),

        # ------------------------------------------------------------------
        #  2 – Piano lesson (fixed Thursday 18:00‑19:00)
        # ------------------------------------------------------------------
        _Activity(
            name='Piano',
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=60,
            max_block_minutes=60,
            min_start_minutes=0,            # not used – fixed overrides it
            fixed=[(3, 18*60, 60)],          # Thursday 18:00‑19:00
            priority=3,
        ),

        # ------------------------------------------------------------------
        #  3 – Exercise (early‑morning, 2×/week)
        # ------------------------------------------------------------------
        _Activity(
            name='Exercise',
            frequency=2,
            even_spacing=False,
            min_weekly_minutes=120,
            max_block_minutes=60,
            min_start_minutes=5*60,         # cannot start before 05:00
            fixed=[],
            priority=1,
        ),

        # ------------------------------------------------------------------
        #  4 – Yoga (morning, 2×/week, try to spread)
        # ------------------------------------------------------------------
        _Activity(
            name='Yoga',
            frequency=2,
            even_spacing=True,
            min_weekly_minutes=90,
            max_block_minutes=60,
            min_start_minutes=6*60,
            fixed=[],
            priority=2,
        ),

        # ------------------------------------------------------------------
        #  5 – Cooking (evenings, 3×/week)
        # ------------------------------------------------------------------
        _Activity(
            name='Cooking',
            frequency=3,
            even_spacing=False,
            min_weekly_minutes=180,
            max_block_minutes=120,
            min_start_minutes=17*60,
            fixed=[],
            priority=3,
        ),

        # ------------------------------------------------------------------
        #  6 – Grocery shopping (once a week, midday)
        # ------------------------------------------------------------------
        _Activity(
            name='Groceries',
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=60,
            max_block_minutes=60,
            min_start_minutes=10*60,
            fixed=[],
            priority=4,
        ),

        # ------------------------------------------------------------------
        #  7 – Cleaning (once a week, morning)
        # ------------------------------------------------------------------
        _Activity(
            name='Cleaning',
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=120,
            max_block_minutes=120,
            min_start_minutes=9*60,
            fixed=[],
            priority=4,
        ),

        # ------------------------------------------------------------------
        #  8 – Laundry (once a week, early‑morning)
        # ------------------------------------------------------------------
        _Activity(
            name='Laundry',
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=60,
            max_block_minutes=60,
            min_start_minutes=8*60,
            fixed=[],
            priority=4,
        ),

        # ------------------------------------------------------------------
        #  9 – Reading (evenly spaced, night, 3×/week)
        # ------------------------------------------------------------------
        _Activity(
            name='Reading',
            frequency=3,
            even_spacing=True,
            min_weekly_minutes=180,
            max_block_minutes=90,
            min_start_minutes=20*60,
            fixed=[],
            priority=5,
        ),

        # ------------------------------------------------------------------
        # 10 – Spanish (language learning, 2×/week, evening)
        # ------------------------------------------------------------------
        _Activity(
            name='Spanish',
            frequency=2,
            even_spacing=True,
            min_weekly_minutes=120,
            max_block_minutes=60,
            min_start_minutes=19*60,
            fixed=[],
            priority=5,
        ),
    ]

    blocks, table, activity_to_blocks, day_load = greedy_initial(activities)

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

    annealer = Annealer(
        table=table,
        activities=activities,
        blocks=blocks,
        atb=activity_to_blocks,
        day_load=day_load
        )
    result_table, result_blocks, result_cost = annealer.simulate_annealing(table)

    print('RESULTS =======================================')

    for day in range(SCHEDULE_SIZE):
        print(f'----- day {day}-------------------')
        day_blocks = [b for b in result_blocks.values() if b.day == day]
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
    print(f'Cost {result_cost}')