import math
import random
from datetime import datetime
from typing import Optional

# from  import Block

type State = list[list[int]]


class Activity:
    id_registry = 0
    def __init__(self, title:str='Activity', start_slot=5, end_slot=20) -> None:
        self.id = self.generate_id()
        self.title = title
        self.frequency = (1,7,random.randint(0,6))
        self.start_slot = start_slot
        self.end_slot = end_slot

    @classmethod
    def generate_id(cls)->int:
        cls.id_registry = cls.id_registry+1
        return cls.id_registry

    def __str__(self) -> str:
        return f"<Activity {self.id}: {self.title}"


class _Block:
    id_registry = 0

    def __init__(self,
                day,
                start_slot,
                end_slot,
                start_day=0,
                end_day=0,
                activity_id=-1
                ) -> None:
        self.id = self.generate_id()
        self.immovable = True
        self.activity_id = activity_id

        self.start_day = start_day
        self.end_day = end_day
        self.start_slot = start_slot
        self.end_slot = end_slot
        self.slot_length = start_slot-end_slot
        self.day = day

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





# plan
# use simulated annealing <3
# algo coming in clutch

# parameters
DAYS = 7
MINS_IN_DAY = 24 * 60
SLOT_SIZE = 60 #mins
SLOTS_PER_DAY = int(MINS_IN_DAY/SLOT_SIZE)

#penalty modifs
HARD = math.inf
HARD_SOFT = 100.0
SOFT = 10.0
NORMAL = 1.0

# vars

TIMETABLE: State = [ [ -1 for y in range( SLOTS_PER_DAY ) ] for x in range( DAYS ) ]


INITIAL_TEMPERATURE = 1e6
T = INITIAL_TEMPERATURE
T_MIN = 1e-5 # need to tweak to find optimal
a = 0.95 # cooling factor

state_previous:list[_Block] = []
# need to generate initial solution, get user to do it instead?

block_lookup:dict[int, _Block] = {}
activity_lookup:dict[int, Activity] = {}
occupancy:dict[tuple[int,int], int] = {}
activity_to_blocks:dict[int, set[int]] = {}

def register_activity(a: Activity):
    activity_lookup[a.id]=a

def unregister_activity(a: Activity):
    activity_lookup.pop(a.id)


def register_block(b: _Block):
    activity_to_blocks[b.activity_id].add(b.id)

def unregister_block(b: _Block):
    activity_to_blocks[b.activity_id].remove(b.id)

def clear_block(b:_Block):
    for slot in range(b.start_slot, b.start_slot + b.slot_length):
        occupancy[(b.day,slot)] = -1
    unregister_block(b)

def can_place(state:State, b:_Block):
    for slot in range(b.start_slot, b.start_slot + b.slot_length):
        if state[b.day][slot] not in {-1, b.id}:
            return False
    return True

def place_block(state:State, b: _Block):
    for slot in range(b.start_slot, b.end_slot):
        state[b.day][slot] = b.id
    return state

def generate_initial_solution(activities: dict[int, Activity])->State:
    solution:State = TIMETABLE
    for activity in activities.values():
        for current_day in range(DAYS):
            if current_day % (activity.frequency[0]*activity.frequency[1])==activity.frequency[2]:
                block = _Block(day=current_day, start_slot=activity.start_slot, end_slot=activity.end_slot, activity_id=activity.id)
                print(block)
                if can_place(solution, block):
                    print(f'placing {block} at {current_day}:{activity.start_slot}:{activity.end_slot}')
                    solution = place_block(solution, block)
    return solution


def cool(T):
    return T*a

def generate_new_neighbour(state: list[_Block]):
    return

# different changes
def shift_move(state)->tuple[State,float]:
    # shift a block one day before or after, and shift it by k hours (random)
    delta_cost = 0
    return state, delta_cost

def resize_block(state)->tuple[State,float]:
    # change the length of a block by 1 slot
    delta_cost = 0
    return state, delta_cost

def swap_blocks(state)->tuple[State,float]:
    # swap two blocks of different activities
    delta_cost = 0
    return state, delta_cost

def split_move(state)->tuple[State,float]:
    # if length>max length, split block
    delta_cost = 0
    return state, delta_cost

def random_reschedule(state)->tuple[State,float]:
    # completely delete an activity's blocks and re-insert using greedy (lowest priority)
    delta_cost = 0
    return state, delta_cost


def propose_change(state: State)->tuple[State,float]:
    change_type = random.choice(['shift', 'resize', 'swap', 'split', 'random'])
    match change_type:
        case 'shift':
            return shift_move(state)
        case 'resize':
            return resize_block(state)
        case 'swap':
            return swap_blocks(state)
        case 'split':
            return split_move(state)
        case 'random':
            return random_reschedule(state)
    return state, math.inf

def revert_change():
    return state_previous

def _cost(state: State)->float:
    return 0.0

def simulated_annealing(state0: State, T:float):
    s_current = state0
    best = (state0, _cost(state0))
    while T > T_MIN:
        s_new, delta_cost = propose_change(s_current)

        if delta_cost <= 0 or random.random() < math.exp(-delta_cost/T):
            s_current = s_new
            cost = _cost(state0)
            if cost < best[1]: # type: ignore
                best = (s_current, cost)
        T = cool(T)

    return best


acts:list[str] =[]
for i in range(4):
    a = Activity(title=f'Activty {i}')
    acts.append(str(a))
    register_activity(a)


print('a: ', acts)
print('t: ', generate_initial_solution(activity_lookup))