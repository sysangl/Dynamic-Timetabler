import math
import random

# from  import Block

type Table = list[list[int | None]]


class Activity:
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
        self.name : str = name
        self.frequency:int = frequency
        self.even_spacing:bool = even_spacing
        self.min_weekly_minutes: int = min_weekly_minutes
        self.max_block_minutes: int = max_block_minutes
        self.min_start_minutes: int = min_start_minutes
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
        return f"<Activity {self.id}: {self.name}"


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
        self.start:int=start
        self.length:int=length
        self.day:int=day

    @classmethod
    def generate_id(cls)->int:
        cls.id_registry = cls.id_registry+1
        return cls.id_registry

    def __str__(self) -> str:
        return f"<Block {self.id}: Activity {self.activity_id}>"

    # def _convert_to_db_block(self)->Block|None:
    #     return None
    #     b = Block(
    #     )
    #     return b


# parameters
DAYS = 7
SCHEDULE_SIZE = 7
MINS_IN_DAY = 24 * 60
SLOT_SIZE = 30 #mins
SLOTS_PER_DAY = MINS_IN_DAY//SLOT_SIZE

INITIAL_TEMPERATURE = 1e6
T = INITIAL_TEMPERATURE
T_MIN = 1e-5 # need to tweak to find optimal
C_F = 0.95 # cooling factor

MAX_PRIORITY = 10
#penalty modifs
HARD = math.inf
HARD_SOFT = 100.0
SOFT = 10.0
NORMAL = 1.0



table_previous:list[_Block] = []
# need to generate initial solution, get user to do it instead?



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
        if table[b.day][slot] not in {None, b.id}:
            return False
    return True

def place_block(table:Table, b: _Block):
    for slot in range(b.start, b.start + b.length):
        table[b.day][slot] = b.id
    return table

def schedule_activity(activity:Activity, table:Table, blocks:dict[int, _Block], activity_to_blocks:dict[int, set[int]], day_load:list[int]):
    print(f'Scheduling activity {activity.name} (id={activity.id})')
    
    needed_sessions = max(activity.frequency, 1)

    total_needed = max(activity.min_weekly_slots, needed_sessions)

    lengths = allocate_lengths(total_needed, needed_sessions, activity.max_block_slots)
    print(f'lengths: {lengths}')
    used_days: set[int] = set()


    if activity.even_spacing:
        target_days = [min(max(0, round(i * SCHEDULE_SIZE / needed_sessions)), SCHEDULE_SIZE-1) for i in range(needed_sessions)]
    else:
        target_days = [None] * needed_sessions

    print(f'tdays : {target_days}')

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

        print(f'l {idx} cdays : {candidate_days}')
        print(f'min start : {activity.min_start_slot}')

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


def place_fixed_blocks(table:Table, activities: list[Activity], blocks: dict[int,_Block], activity_to_blocks:dict[int, set[int]], day_load:list[int]):
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

def greedy_initial(activities: list[Activity], schedule_size:int=SCHEDULE_SIZE, slots_per_day:int=SLOTS_PER_DAY, slot_size:int=SLOT_SIZE):
    table: Table = [[None for _ in range(slots_per_day) ] for _ in range(SCHEDULE_SIZE)]
    blocks: dict[int, _Block] = {}
    activity_to_blocks:dict[int, set[int]] = {}
    for a in activities:
        activity_to_blocks[a.id] = set()
    day_load:list[int] = [0]*SCHEDULE_SIZE

    place_fixed_blocks(table, activities, blocks, activity_to_blocks, day_load)

    sorted_activities = sorted(activities, key=lambda a: (a.priority, -int(a.even_spacing), -a.min_weekly_minutes))

    for a in sorted_activities:
        if len(a.fixed_blocks) >= a.frequency:
            continue
        schedule_activity(a, table, blocks, activity_to_blocks, day_load)

    return blocks, table, activity_to_blocks

if __name__ == "__main__":
    # ai -generated activities
    activities = [
        # ------------------------------------------------------------------
        #  0 – Full‑time work (fixed 9 am‑5 pm Mon‑Fri)
        # ------------------------------------------------------------------
        Activity(
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
        Activity(
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
        Activity(
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
        Activity(
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
        Activity(
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
        Activity(
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
        Activity(
            name='Grocery Shopping',
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
        Activity(
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
        Activity(
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
        Activity(
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
        Activity(
            name='Spanish',
            frequency=2,
            even_spacing=True,
            min_weekly_minutes=120,
            max_block_minutes=60,
            min_start_minutes=19*60,
            fixed=[],
            priority=5,
        ),

        # ------------------------------------------------------------------
        # 11 – Programming (evenly spaced, night, 3×/week)
        # ------------------------------------------------------------------
        Activity(
            name='Programming',
            frequency=3,
            even_spacing=True,
            min_weekly_minutes=300,
            max_block_minutes=180,
            min_start_minutes=18*60,
            fixed=[],
            priority=2,
        ),

        # ------------------------------------------------------------------
        # 12 – Meditation (daily, early‑morning, 30 min)
        # ------------------------------------------------------------------
        Activity(
            name='Meditation',
            frequency=7,
            even_spacing=True,
            min_weekly_minutes=30,
            max_block_minutes=30,
            min_start_minutes=6*60,
            fixed=[],
            priority=1,
        ),

        # ------------------------------------------------------------------
        # 13 – Gardening (twice a week, morning)
        # ------------------------------------------------------------------
        Activity(
            name='Gardening',
            frequency=2,
            even_spacing=False,
            min_weekly_minutes=180,
            max_block_minutes=180,
            min_start_minutes=9*60,
            fixed=[],
            priority=4,
        ),

        # ------------------------------------------------------------------
        # 14 – Dog Walking (six short walks a week, mornings)
        # ------------------------------------------------------------------
        Activity(
            name='Dog Walking',
            frequency=6,
            even_spacing=False,
            min_weekly_minutes=180,
            max_block_minutes=30,
            min_start_minutes=7*60,
            fixed=[],
            priority=3,
        ),

        # ------------------------------------------------------------------
        # 15 – Family Time (evenings, twice a week)
        # ------------------------------------------------------------------
        Activity(
            name='Family Time',
            frequency=2,
            even_spacing=False,
            min_weekly_minutes=300,
            max_block_minutes=180,
            min_start_minutes=19*60,
            fixed=[],
            priority=2,
        ),

        # ------------------------------------------------------------------
        # 16 – Friends Meet (fixed Saturday night)
        # ------------------------------------------------------------------
        Activity(
            name='Friends Meet',
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=120,
            max_block_minutes=180,
            min_start_minutes=0,
            fixed=[(5, 18*60, 180)],   # Saturday 18:00‑21:00
            priority=3,
        ),

        # ------------------------------------------------------------------
        # 17 – Movie Night (fixed Sunday night)
        # ------------------------------------------------------------------
        Activity(
            name='Movie Night',
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=180,
            max_block_minutes=180,
            min_start_minutes=0,
            fixed=[(6, 20*60, 180)],   # Sunday 20:00‑23:00
            priority=4,
        ),

        # ------------------------------------------------------------------
        # 18 – Volunteer (once a week, mid‑morning)
        # ------------------------------------------------------------------
        Activity(
            name='Volunteer',
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=240,
            max_block_minutes=240,
            min_start_minutes=9*60,
            fixed=[],
            priority=3,
        ),

        # ------------------------------------------------------------------
        # 19 – Gaming (late‑night, 3×/week)
        # ------------------------------------------------------------------
        Activity(
            name='Gaming',
            frequency=3,
            even_spacing=False,
            min_weekly_minutes=240,
            max_block_minutes=120,
            min_start_minutes=22*60,
            fixed=[],
            priority=5,
        ),

        # ------------------------------------------------------------------
        # 20 – Music Practice (instrument, 2×/week, early‑evening)
        # ------------------------------------------------------------------
        Activity(
            name='Music Practice',
            frequency=2,
            even_spacing=False,
            min_weekly_minutes=120,
            max_block_minutes=60,
            min_start_minutes=16*60,
            fixed=[],
            priority=3,
        ),
    ]

    blocks, table, activity_to_blocks = greedy_initial(activities)

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


# 
# simultaed annealing
# 

def cool(T):
    return T*C_F

def generate_new_neighbour(table: list[_Block]):
    return

# different changes
def shift_move(table)->tuple[Table,float]:
    # shift a block one day before or after, and shift it by k hours (random)
    delta_cost = 0
    
    return table, delta_cost

def resize_block(table)->tuple[Table,float]:
    # change the length of a block by 1 slot
    delta_cost = 0
    return table, delta_cost

def swap_blocks(table)->tuple[Table,float]:
    # swap two blocks of different activities
    delta_cost = 0
    return table, delta_cost

def split_move(table)->tuple[Table,float]:
    # if length>max length, split block
    delta_cost = 0
    return table, delta_cost

def random_reschedule(table)->tuple[Table,float]:
    # completely delete an activity's blocks and re-insert using greedy (lowest priority)
    delta_cost = 0
    return table, delta_cost


def propose_change(table: Table)->tuple[Table,float]:
    change_type = random.choice(['shift', 'resize', 'swap', 'split', 'random'])
    match change_type:
        case 'shift':
            return shift_move(table)
        case 'resize':
            return resize_block(table)
        case 'swap':
            return swap_blocks(table)
        case 'split':
            return split_move(table)
        case 'random':
            return random_reschedule(table)
    return table, math.inf

def revert_change():
    return table_previous

def _cost(table: Table)->float:
    return 0.0

def simulated_annealing(table0: Table, T:float):
    s_current = table0
    best = (table0, _cost(table0))
    while T > T_MIN:
        s_new, delta_cost = propose_change(s_current)

        if delta_cost <= 0 or random.random() < math.exp(-delta_cost/T):
            s_current = s_new
            cost = _cost(table0)
            if cost < best[1]: # type: ignore
                best = (s_current, cost)
        T = cool(T)

    return best

