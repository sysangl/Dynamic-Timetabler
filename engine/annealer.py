import collections
import copy
import math
import random
import sys
from collections.abc import Callable

from classes import (
    ATB,
    LIMIT,
    PENALTY_WEIGHTS,
    ChangeResult,
    Table,
    _Activity,
    _Block,
    _Schedule,
)
from scheduler import can_place, clear_block, place_block


def clamp(value, min_value, max_value):
    return max(min_value,min(value,max_value))


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
        self.balance = 0
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
            cost += (early_oob*2 * PENALTY_WEIGHTS.EARLY_BOUND + late_oob*2 * PENALTY_WEIGHTS.LATE_BOUND)

            if b.start < activity.min_start_slot:
                cost += (b.start-activity.min_start_slot)**2

        # fragmentation (minimise # of blocks)
        if len(block_list) > activity.frequency:
            cost += (len(block_list)-activity.frequency) * PENALTY_WEIGHTS.FRAGMENT

        return cost

    def _idle_penalty(self):
        # cost for not using time
        empty = sum(day.count(None) for day in self.table)
        idle_prev = self.idle
        idle_current = (empty * PENALTY_WEIGHTS.IDLE)/_Schedule.SLOTS_PER_DAY
        self.idle = idle_current
        return idle_current - idle_prev 

    def _balance_penalty(self):
        # penalise for heaping everything into one day
        blocks_per_day = collections.Counter(b.day for b in self.blocks.values())
        total = sum(blocks_per_day)
        balance_current = 0
        for count in blocks_per_day:
            balance_current += (count-(total/_Schedule.SIZE))**2 * PENALTY_WEIGHTS.BALANCE
        balance_prev = self.balance
        self.balance = balance_current
        return balance_current-balance_prev

    def update_activities(self, activity_ids):
        delta = 0
        for a_id in activity_ids:
            old = self.activity_cost[a_id]
            new = self.calculate_cost(a_id)
            self.activity_cost[a_id] = new
            delta += (new - old)

        ## whole table penalties
        delta += self._idle_penalty()
        delta += self._balance_penalty()

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
    movable = [b for b in blocks.values() if not b.fixed]
    if not movable:
        return ChangeResult(LIMIT.HARD,undo=lambda: None)

    block = random.choice(movable)
    activity = activities[block.activity_id]

    old_day = block.day
    old_start = block.start
    affected = {activity.id}

    day_offset = random.choice([-1,0,1])
    start_offset = random.choice(range(-int(_Schedule.SLOTS_PER_DAY//12),int(_Schedule.SLOTS_PER_DAY//12)))
    
    new_day = clamp(old_day+day_offset, 0,_Schedule.SIZE-1)
    new_start = clamp(old_start+start_offset, 0, _Schedule.SLOTS_PER_DAY-1)

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

    if a1 == a2:
        return ChangeResult(LIMIT.HARD, undo=lambda: None)

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

    movable = [b for b in blocks.values() if not b.fixed]
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

    low_prio_activities = [a for a in activities if a.priority <= max_priority_allowed and not a.fixed_blocks]
    if not low_prio_activities:
        return ChangeResult(LIMIT.HARD, undo=lambda: None)



    activity = random.choice(low_prio_activities)


    removed: list[tuple[int, _Block]] = []
    for block_id in list(atb[activity.id]):
        b = blocks[block_id]
        removed.append((block_id, b))
        clear_block(table, b)
        day_load[b.day] -= 1
        del blocks[block_id]
    atb[activity.id].clear()

    old_cost = evaluator.activity_cost[activity.id]

    try:
        scheduler(activity, table, blocks, atb, day_load)
    except RuntimeError:

        for block_id, block in removed:
            place_block(table, block)
            blocks[block_id] = block
            atb[activity.id].add(block_id)
            day_load[block.day] += 1
        evaluator.activity_cost[activity.id] = old_cost
        return ChangeResult(LIMIT.HARD, undo=lambda:None)

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
                                    self.day_load,
                                    self.table
                                    )

        self.T = 100000
        self.T_MIN = 1e-4
        self.cooling = 0.95
        self.cycles = 10000

        self.change_factories = [
            lambda: shift_move(self.table, activities, self.atb,
                            self.blocks, self.day_load, self.evaluator),
            lambda: resize_block(self.table, activities, self.atb,
                                self.blocks, self.day_load, self.evaluator),
            lambda: merge_blocks(self.table, activities, self.atb,
                            self.blocks, self.day_load, self.evaluator),
            lambda: swap_blocks(self.table, activities, self.atb,
                            self.blocks, self.day_load, self.evaluator),
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