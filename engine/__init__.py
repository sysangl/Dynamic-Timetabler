import math

# from app.models.timetable_items import Block

from typing import Optional

import random

from datetime import datetime

type State = list[list[int]]

class Block:
    def __init__(self,
                id:int,
                sdt:datetime,
                edt:datetime,
                ) -> None:
        self.id = id
        self.start_datetime = sdt
        self.end_datetime = edt

b:list[Block] =[]
for i in range(4):
    sdt = datetime(2026,10,7+i, random.randint(1,23),random.randint(0,59))
    edt = datetime(2026,10,7+i, random.randint(1,23),random.randint(0,59))
    if sdt > edt:
        sdt, edt = edt, sdt

    b.append(Block(i, sdt, edt))

# plan
# use simulated annealing <3
# algo coming in clutch

# parameters
DAYS = 7
MINS_IN_DAY = 24 * 60
SLOT_SIZE = 60 #mins

#penalty modifs
HARD = math.inf
HARD_SOFT = 100.0
SOFT = 10.0
NORMAL = 1.0

# vars

TIMETABLE: State = [ [ -1 for y in range( int(MINS_IN_DAY/SLOT_SIZE) ) ] for x in range( DAYS ) ]

blocks: list[Block] = []
INITIAL_TEMPERATURE = 1e6
T = INITIAL_TEMPERATURE
T_MIN = 1e-5 # need to tweak to find optimal
a = 0.95 # cooling factor

state_previous:list[Block] = []
# need to generate initial solution, get user to do it instead?


def get_blocks(blocks)->dict[int, Block]:
    # blocks:list[Block] = Block.query.all()

    tmp:dict[int, Block] = {}
    for block in blocks:
        tmp[block.id]=block
    return tmp


def generate_initial_solution(blocks: dict[int, Block])->State:
    solution:State = TIMETABLE
    for id, block in blocks.items():
        day_start = block.start_datetime.date().weekday()
        mins_start = block.start_datetime.time().hour * 60 + block.start_datetime.time().min.minute

        day_end = block.end_datetime.date().weekday()
        mins_end = block.end_datetime.time().hour * 60 + block.end_datetime.time().min.minute

        current_day = day_start
        current_slot = int(mins_start/SLOT_SIZE)
        while current_day <= day_end:

            solution[current_day][current_slot] = id
            
            current_slot +=1

            if current_slot>=24:
                current_day += 1

            if current_slot==int(mins_end/SLOT_SIZE) and current_day==day_end:
                break
    return solution

print('blocks: ', b)
print('initial: ', generate_initial_solution(get_blocks(b)))

def cool(T):
    return T*a

def generate_new_neighbour(state: list[Block]):
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