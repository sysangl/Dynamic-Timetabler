import collections
import copy
import logging
import math
import random
import sys
from collections.abc import Callable, Iterable

log = logging.getLogger('engine')

from app.engine.classes import (
    AnnealResult,
    ATB,
    LIMIT,
    PENALTY_WEIGHTS,
    ChangeResult,
    OverlapTable,
    _Activity,
    _Block,
    _Schedule,
)

from .scheduler import can_place, clear_block, place_block


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


class CostEvaluator:
    def __init__(
        self,
        schedule: _Schedule,
        activities: dict[int, _Activity],
        blocks: dict[int, _Block],
        atb: ATB,
        day_load: list[int],
        table: OverlapTable,
    ) -> None:

        self.activities:dict[int,_Activity] = activities
        self.blocks:dict[int, _Block] = blocks
        self._blocks_per_day={}
        self.atb:ATB = atb
        self.schedule:_Schedule = schedule
        self.day_load:list[int] = day_load
        self._activity_cost: dict[int, float] = {}

        
        self._idle = 0
        self._balance = 0
        self.table = table

    def _calculate_activity_cost(self, a_id: int)->float:
        activity = self.activities[a_id]
        log.info(f'CE : Calc. Cost {activity.name} [{a_id}]')
        block_list = [self.blocks[bid] for bid in self.atb[a_id]]

        if not block_list:
            return 0.0

        cost = 0
        
        # min time
        total_slots = sum(b.length for b in block_list)
        missing_time = max(0, activity.min_weekly_slots - total_slots)
        cost += missing_time * PENALTY_WEIGHTS.MIN_TIME

        # frequency
        missing_freq = abs(len(block_list) - activity.frequency)
        cost += missing_freq * PENALTY_WEIGHTS.FREQ

        # even spacing
        if activity.even_spacing and len(block_list) > 1:
            days = sorted(b.day for b in block_list)
            ideal = self.schedule.SIZE / activity.frequency
            standard_err = sum(
                (days[day + 1] - days[day] - ideal) for day in range(len(days) - 1)
            )
            cost += standard_err**2 * PENALTY_WEIGHTS.EVEN_SPACING

        # over load
        blocks_per_day = collections.Counter(b.day for b in block_list)
        target = math.ceil(activity.frequency / self.schedule.SIZE)
        for count in blocks_per_day.values():
            if count > target:
                cost += (count - target) * PENALTY_WEIGHTS.OVERLOAD

        for b in block_list:
            # block length
            if b.length > activity.max_block_slots:
                cost += LIMIT.HARD_SOFT
            if b.length < activity.min_block_slots:
                cost += (
                    activity.min_block_slots - b.length
                )**2 * PENALTY_WEIGHTS.MIN_LENGTH

            # bounds
            early_oob = sum(
                abs(slot-self.schedule.EARLY_SLOTS)
                for slot in range(b.start, b.start + b.length)
                if self.schedule.EARLY_SLOTS > slot
            )
            late_oob = sum(
                abs(self.schedule.LATE_SLOTS  < slot)
                for slot in range(b.start, b.start + b.length)
                if self.schedule.LATE_SLOTS < slot
            )
            cost += (
                early_oob**2 * PENALTY_WEIGHTS.EARLY_BOUND
                + late_oob**2 * PENALTY_WEIGHTS.LATE_BOUND
            )

            # high cost bounds / user defined
            bounds = self.schedule.HIGH_COST_BOUNDS.get(b.day, [])
            for bound in bounds:
                hcb = sum(
                    1
                    for slot in range(b.start, b.start + b.length)
                    if bound[0] <= slot <= bound[1]
                )
                cost += hcb * PENALTY_WEIGHTS.HIGH_COST_BOUND

            # preferred days
            if b.day not in activity.preferred_days:
                cost += PENALTY_WEIGHTS.PREFERRED_DAYS

            # user defined
            for bound in self.schedule.user_defined_bounds.values():
                if len(set(range(b.start, b.start + b.length)).intersection(set(range(bound[1],bound[1]+bound[2])))) != 0:
                    cost += bound[1] * PENALTY_WEIGHTS.HIGH_COST_BOUND

            # minimum start
            if b.start < activity.min_start_slot:
                cost += (b.start - activity.min_start_slot) ** 2 * PENALTY_WEIGHTS.MIN_START

        # fragmentation (minimise # of blocks)
        cost += len(block_list)/activity.schedule.SIZE * PENALTY_WEIGHTS.FRAGMENT

        return cost

    def _idle_delta(self) -> float:
        delta = 0.0

        empty_slots = sum(1 for day in self.table for slot in day if len(slot) == 0)
        idle_current = (empty_slots * PENALTY_WEIGHTS.IDLE) / self.schedule.SLOTS_PER_DAY
        delta += idle_current - self._idle
        self._idle = idle_current

        return delta

    def _balance_delta(self) -> float:
        delta = 0.0
        slots_per_day = collections.Counter(
            [b.day for b in self.blocks.values() for _ in range(b.start, b.start+b.length)]
        )
        total_slots = sum(slots_per_day.values())
        balance_current = sum(
            (count - total_slots / self.schedule.SIZE) ** 2
            for count in slots_per_day.values()
        ) * PENALTY_WEIGHTS.BALANCE
        delta += balance_current - self._balance
        self._balance = balance_current
        return delta

    def _compute_idle_penalty(self):
        empty_slots = sum(
            1 for day in self.table
            for slot in day if len(slot) == 0
        )
        return (empty_slots * PENALTY_WEIGHTS.IDLE) / self.schedule.SLOTS_PER_DAY

    def _compute_balance_penalty(self):
        slots_per_day = collections.Counter(
            [b.day for b in self.blocks.values() for _ in range(b.start, b.start+b.length)]
        )
        total_slots = sum(slots_per_day.values())
        return sum(
            (count - total_slots / self.schedule.SIZE) ** 2
            for count in slots_per_day.values()
        ) * PENALTY_WEIGHTS.BALANCE
    def update_activities(self, activity_ids:Iterable[int]):
        delta = 0
        for a_id in activity_ids:
            old = self.activity_cost(a_id)
            new = self._calculate_activity_cost(a_id)
            self._activity_cost[a_id] = new
            delta += new - old

        ## whole table penalties
        delta += self._idle_delta()
        delta += self._balance_delta()

        return delta

    def recompute_all(self):
        log.info("CE : Recomputing all")
        self._activity_cost = {aid: self._calculate_activity_cost(aid) for aid in self.activities}

        for aid in self.activities:
            self._blocks_per_day[aid] = collections.Counter(self.blocks[bid].day for bid in self.atb.get(aid, set()))


        self.idle = self._compute_idle_penalty()
        self.balance = self._compute_balance_penalty()

    @property
    def total_cost(self)->float:
        return sum(self._activity_cost.values())

    def activity_cost(self, aid:int) -> float:
        return self._activity_cost.get(aid,0.0)

# different changes
def shift_move(
    table: OverlapTable,
    activities: dict[int, _Activity],
    atb: ATB,
    blocks: dict[int, _Block],
    day_load: list[int],
    evaluator: CostEvaluator,
) -> ChangeResult:
    # shift a block one day before or after, and shift it by k hours (random)
    movable = [b for b in blocks.values() if not b.fixed]
    if not movable:
        return ChangeResult(LIMIT.HARD, undo=lambda: None, accept=lambda: None)


    block = random.choice(movable)
    activity = activities[block.activity_id]

    old_day = block.day
    old_start = block.start
    affected = {activity.id}

    day_offset = random.choice([-1, 0, 1])
    start_offset = random.choice(
        range(
            -int(activity.schedule.SLOTS_PER_DAY // 12),
            int(activity.schedule.SLOTS_PER_DAY // 12),
        )
    )

    new_day = clamp(old_day + day_offset, 0, activity.schedule.SIZE - 1)
    new_start = clamp(old_start + start_offset, 0, activity.schedule.SLOTS_PER_DAY - 1)

    # if new_start < activity.min_start_slot:
    #     return ChangeResult(LIMIT.HARD, undo=lambda: None, accept=lambda: None) # maybe make the penalty scale with prio? or use the soft hard hybrid

    test_block = _Block(
        activity_id=activity.id, day=new_day, start=new_start, length=block.length
    )
    if not can_place(activity.schedule, table, test_block):
        return ChangeResult(LIMIT.HARD, undo=lambda: None, accept=lambda: None)

    clear_block(table, block)
    day_load[old_day] -= 1
    block.day = new_day
    block.start = new_start
    place_block(table, block)
    day_load[new_day] += 1

    delta_cost = evaluator.update_activities(affected)

    def undo():
        clear_block(table, block)
        day_load[new_day] -= 1
        block.day = old_day
        block.start = old_start
        place_block(table, block)
        day_load[old_day] += 1

        evaluator.update_activities(affected)

    def accept():
        log.info(f'Accepted SHIFT of {activity.name}[{activity.id}]:{block.id} ')

    return ChangeResult(delta=delta_cost, undo=undo,accept=accept)

def slide_move(
    table: OverlapTable,
    activities: dict[int, _Activity],
    atb: ATB,
    blocks: dict[int, _Block],
    day_load: list[int],
    evaluator: CostEvaluator,
) -> ChangeResult:
    # shift a block one day before or after, and shift it by k hours (random)
    movable = [b for b in blocks.values() if not b.fixed]
    if not movable:
        return ChangeResult(LIMIT.HARD, undo=lambda: None, accept=lambda: None)


    block = random.choice(movable)
    activity = activities[block.activity_id]

    old_start = block.start
    start = block.start
    affected = {activity.id}


    while start < activity.schedule.SLOTS_PER_DAY - block.length:
        test_block = _Block(
            activity_id=activity.id,
            day=block.day,
            start=start,
            length=block.length
        )
        if can_place(activity.schedule, table, test_block):
            break
        start += 1

    if start < activity.schedule.SLOTS_PER_DAY - block.length:
        return ChangeResult(LIMIT.HARD, undo=lambda: None, accept=lambda: None)

    clear_block(table, block)
    block.start = start
    place_block(table, block)
    delta_cost = evaluator.update_activities(affected)


    def undo():
        clear_block(table, block)
        block.start = old_start
        place_block(table, block)
        evaluator.update_activities(affected)

    def accept():
        log.info(f'Accepted SLIDE of {activity.name}[{activity.id}]:{block.id} ')

    return ChangeResult(delta=delta_cost, undo=undo,accept=accept)

def swap_blocks(
    table: OverlapTable,
    activities: dict[int, _Activity],
    atb: ATB,
    blocks: dict[int, _Block],
    day_load: list[int],
    evaluator: CostEvaluator,
) -> ChangeResult:
    # swap two blocks of different activities
    delta_cost = 0

    b1 = random.choice([b for b in blocks.values() if not b.fixed])
    b2 = random.choice([b for b in blocks.values() if not b.fixed])

    if b1 == b2:
        return ChangeResult(LIMIT.HARD, undo=lambda: None, accept=lambda: None)

    a1 = activities[b1.activity_id]
    a2 = activities[b2.activity_id]

    if a1 == a2:
        return ChangeResult(LIMIT.HARD, undo=lambda: None, accept=lambda: None)


    old1 = (b1.day, b1.start)
    old2 = (b2.day, b2.start)
    affected = {a1.id, a2.id}

    test1 = _Block(
        id=b1.id,
        activity_id=b2.activity_id,
        day=b2.day,
        start=b2.start,
        length=b1.length,
    )
    test2 = _Block(
        id=b2.id,
        activity_id=b1.activity_id,
        day=b1.day,
        start=b1.start,
        length=b2.length,
    )

    if not (
        can_place(a1.schedule, table, test1) and can_place(a2.schedule, table, test2)
    ):
        return ChangeResult(LIMIT.HARD, undo=lambda: None, accept=lambda: None)

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

    def accept():
        log.info(f'Accepted SWAP of {a1.name}[{a1.id}]:{b1.id} & {a2.name}[{a2.id}]:{b2.id}')

    return ChangeResult(delta=delta_cost, undo=undo,accept=accept)


def resize_block(
    table: OverlapTable,
    activities: dict[int, _Activity],
    atb: ATB,
    blocks: dict[int, _Block],
    day_load: list[int],
    evaluator: CostEvaluator,
) -> ChangeResult:
    # change the length of a block by 1 slot

    movable = [b for b in blocks.values() if not b.fixed]
    if not movable:
        return ChangeResult(LIMIT.HARD, undo=lambda: None, accept=lambda: None)
    


    block = random.choice(movable)
    activity = activities[block.activity_id]

    old_length = block.length
    affected = {activity.id}

    direction = random.choice([-1, 1])

    def accept():
        log.info(f'Accepted RESIZE for {activity.name}[{activity.id}]:{block.id}')
    
    def undo():
        clear_block(table, block)
        block.length = old_length
        place_block(table, block)
        evaluator.update_activities(affected)

    if direction == -1:
        if block.length == 1:
            return ChangeResult(LIMIT.HARD, undo=lambda: None, accept=lambda: None)
        clear_block(table, block)
        block.length -= 1
        place_block(table, block)
        delta_cost = evaluator.update_activities(affected)
        return ChangeResult(delta_cost, undo=undo, accept=lambda: accept)

    if block.length + 1 > activity.max_block_slots:
        return ChangeResult(LIMIT.SOFT, undo=lambda: None, accept=lambda: None)

    next_slot = block.start + block.length
    if next_slot >= activity.schedule.SLOTS_PER_DAY:
        return ChangeResult(LIMIT.HARD, undo=lambda: None, accept=lambda: None)
    if len(table[block.day][next_slot])!=0:
        return ChangeResult(LIMIT.HARD, undo=lambda: None, accept=lambda: None)

    clear_block(table, block)
    block.length += 1
    place_block(table, block)
    delta_cost = evaluator.update_activities(affected)


    return ChangeResult(delta=delta_cost, undo=undo, accept=accept)


def split_block(
    table: OverlapTable,
    activities: dict[int, _Activity],
    atb: ATB,
    blocks: dict[int, _Block],
    day_load: list[int],
    evaluator: CostEvaluator,
) -> ChangeResult:
    # if length>max length, split block

    oversized = [
        b
        for b in blocks.values()
        if b.length > activities[b.activity_id].max_block_slots
        and not b.fixed
    ]

    if not oversized:
        return ChangeResult(LIMIT.HARD, undo=lambda: None, accept=lambda: None)



    parent = random.choice(oversized)
    activity = activities[parent.activity_id]

    parent_copy = _Block(
        id=parent.id,
        activity_id=parent.activity_id,
        day=parent.day,
        start=parent.start,
        length=parent.length,
    )

    split_point = random.randint(1, parent.length - 1)

    child1 = _Block(
        activity_id=parent.activity_id,
        day=parent.day,
        start=parent.start,
        length=split_point,
    )
    child2 = _Block(
        activity_id=parent.activity_id,
        day=parent.day,
        start=parent.start + split_point,
        length=parent.length - split_point,
    )

    clear_block(table, parent)
    day_load[parent.day] -= 1
    schedule = activities[parent.activity_id].schedule
    # check placement
    # restore
    if not (can_place(schedule, table, child1) and can_place(schedule, table, child2)):
        place_block(table, parent)
        day_load[parent.day] += 1
        return ChangeResult(delta=LIMIT.HARD, undo=lambda: None, accept=lambda: None)

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

    def accept():
        log.info(f'Accepted SPLIT for {activity.name}[{activity.id}]:{parent.id}')

    return ChangeResult(delta_cost, undo=undo, accept=accept)


def merge_blocks(
    table: OverlapTable,
    activities: dict[int, _Activity],
    atb: ATB,
    blocks: dict[int, _Block],
    day_load: list[int],
    evaluator: CostEvaluator,
) -> ChangeResult:

    candidates: list[tuple[_Activity, _Block, _Block]] = []

    for aid, a in activities.items():
        if len(atb[aid]) <= a.frequency:
            continue
        blocks_in_day: dict[int, list[_Block]] = {}
        for bid in atb[aid]:
            b = blocks[bid]
            if not b.fixed:
                blocks_in_day.setdefault(b.day, []).append(b)

        for block_list in blocks_in_day.values():
            block_list.sort(key=lambda b: b.start)
            for i in range(len(block_list) - 1):
                b1, b2 = block_list[i], block_list[i + 1]

                if b1.start + b1.length == b2.start:
                    candidates.append((a, b1, b2))

    if not candidates:
        return ChangeResult(LIMIT.HARD, undo=lambda: None, accept=lambda: None)



    activity, b1, b2 = random.choice(candidates)

    old_b1 = _Block(
        id=b1.id,
        activity_id=b1.activity_id,
        day=b1.day,
        start=b1.start,
        length=b1.length,
    )

    old_b2 = _Block(
        id=b2.id,
        activity_id=b2.activity_id,
        day=b2.day,
        start=b2.start,
        length=b2.length,
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

    affected = {activity.id}

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

    def accept():
        log.info(f'Accepted MERGE for {activity.name}[{activity.id}]:{b1.id} & {b2.id}')

    return ChangeResult(delta_cost, undo=undo, accept=accept)


def random_reschedule(
    table: OverlapTable,
    activities: dict[int, _Activity],
    atb: ATB,
    blocks: dict[int, _Block],
    day_load: list[int],
    evaluator: CostEvaluator,
    scheduler: Callable,
    max_priority_allowed: int = 5,
) -> ChangeResult:

    # return  # type: ignore
    
    # completely delete an activity's blocks and re-insert using greedy (lowest priority)

    low_prio_activities = [
        a
        for a in activities.values()
        if a.priority <= max_priority_allowed and not a.fixed
    ]
    if not low_prio_activities:
        return ChangeResult(LIMIT.HARD, undo=lambda: None, accept=lambda: None)



    activity = random.choice(low_prio_activities)

    removed: list[tuple[int, _Block]] = []
    for block_id in list(atb[activity.id]):
        b = blocks[block_id]
        removed.append((block_id, b))
        clear_block(table, b)
        day_load[b.day] -= 1
        del blocks[block_id]
    atb[activity.id].clear()

    old_cost = evaluator.activity_cost(activity.id)

    try:
        scheduler(activity, table, blocks, atb, day_load)
    except RuntimeError:
        for block_id, block in removed:
            place_block(table, block)
            blocks[block_id] = block
            atb[activity.id].add(block_id)
            day_load[block.day] += 1
        evaluator.recompute_all()
        return ChangeResult(LIMIT.HARD, undo=lambda: None, accept=lambda: None)

    new_cost = evaluator._calculate_activity_cost(activity.id)
    evaluator._activity_cost[activity.id] = new_cost
    delta_cost = new_cost - old_cost

    def undo():
        for block_id in list(atb[activity.id]):
            block = blocks[block_id]
            clear_block(table, block)
            day_load[block.day] -= 1
            del blocks[block_id]
        atb[activity.id].clear()

        for block_id, block in removed:
            place_block(table, block)
            blocks[block_id] = block
            atb[activity.id].add(block_id)

        evaluator._activity_cost[activity.id] = old_cost
        evaluator.recompute_all()

    def accept():
        log.info(f'Accepted RESCHEDULE for {activity.name}[{activity.id}]')

    return ChangeResult(delta_cost, undo=undo,accept=accept)


class Annealer:
    def __init__(
        self,
        schedule: _Schedule,
        table: OverlapTable,
        activities: list[_Activity],
        atb: ATB,
        blocks: dict[int, _Block],
        day_load: list[int],
        scheduler: Callable[
            [_Activity, OverlapTable, dict[int, _Block], ATB, list[int]], None
        ],
        mode:str='normal',
        log:bool=False
    ) -> None:
        self.activities = {a.id: a for a in activities}
        self.scheduler = scheduler

        self.table = table
        self.blocks = blocks
        self.atb = atb
        self.day_load = day_load

        self.evaluator = CostEvaluator(
            schedule, self.activities, self.blocks, self.atb, self.day_load, self.table
        )
        self.evaluator.recompute_all()

        self.T = 1e26
        self.T_MIN = 1e-3
        self.cooling = 0.999
        self.cycles = 500
        self.adjust_interval = 200
        self.target_acceptance = 0.18
        self.adjust_factor = 0.99
        self.change_success_rate = 0.4

        self.schedule = schedule

        self.log = log

        self.change_factories = [
            # ('shift', lambda: shift_move(
            #     self.table,
            #     self.activities,
            #     self.atb,
            #     self.blocks,
            #     self.day_load,
            #     self.evaluator,
            # )),
            ('slide', lambda: slide_move(
                self.table,
                self.activities,
                self.atb,
                self.blocks,
                self.day_load,
                self.evaluator,
            )),
            ('resize',lambda: resize_block(
                self.table,
                self.activities,
                self.atb,
                self.blocks,
                self.day_load,
                self.evaluator,
            )),
            ('merge',lambda: merge_blocks(
                self.table,
                self.activities,
                self.atb,
                self.blocks,
                self.day_load,
                self.evaluator,
            )),
            ('split',lambda: split_block(
                self.table,
                self.activities,
                self.atb,
                self.blocks,
                self.day_load,
                self.evaluator,
            )),
            ('swap',lambda: swap_blocks(
                self.table,
                self.activities,
                self.atb,
                self.blocks,
                self.day_load,
                self.evaluator,
            )),
            ('random',lambda: random_reschedule(
                self.table,
                self.activities,
                self.atb,
                self.blocks,
                self.day_load,
                self.evaluator,
                self.scheduler,
                max_priority_allowed=5,
            )),
        ]

        self.change_stats = {
            # 'shift':0.0,
            'slide':0.0,
            'resize':0.0,
            'merge':0.0,
            'swap':0.0,
            'split':0.0,
            'random':0.0,
        }

    def _weighted_change_factory(self,T): # type: ignore
        base = [0.15] * len(self.change_stats)

        for c in self.change_stats:
            self.change_stats[c] *= 0.9

        for i, (c, success_rate) in enumerate(self.change_stats.items()):
            if success_rate > self.change_success_rate:
                base[i] *= 1.5
        return random.choices(self.change_factories, weights=base)[0]

    def log_cool(self, T, iteration):
        return T / math.log(1+iteration)

    def exp_cool(self, T, iteration):
        return T * (self.cooling ** iteration)

    def dynamic_cool(self, T, iteration):
        if T > self.T * 0.2:
            return self.exp_cool(T, iteration)
        else:
            return self.log_cool(T, iteration)


    def run(self)->AnnealResult:
        log.info(f'Starting ANNEAL for {self.schedule.db_id}')
        best_cost = self.evaluator.total_cost
        best_table = copy.deepcopy(self.table)
        best_blocks = copy.deepcopy(self.blocks)

        cost_updates = 0
        iteration_count = 0
        accepted = 0
        attempted = 0

        T = self.T

        while T > self.T_MIN:
            for _ in range(self.cycles):
                attempted += 1
                change_name, change_fn = self._weighted_change_factory(T)
                change = change_fn()
                delta_cost = change.delta                
                if delta_cost <= 0 or (random.random() < math.exp(-delta_cost / T)):
                    accepted += 1
                    change.accept()
                    self.change_stats[change_name] += 1
                    if self.evaluator.total_cost < best_cost:
                        best_cost = self.evaluator.total_cost
                        best_table = copy.deepcopy(self.table)
                        best_blocks = copy.deepcopy(self.blocks)
                        cost_updates += 1
                        if self.log:
                            sys.stdout.write(
                                f"\r<T{round(T,4)!s:15s}> [{cost_updates!s:8s}] {best_cost:8.4f}"
                            )
                            sys.stdout.flush()
                else:
                    change.undo()

                # if iteration_count % self.adjust_interval == 0:
                #     accept_ratio = accepted/attempted
                #     if accept_ratio > self.target_acceptance:
                #         T *= self.adjust_factor
                #     else:
                #         T /= self.adjust_factor
                #     accepted = 0
                #     attempted = 0

                iteration_count += 1
                T = self.dynamic_cool(self.T,iteration_count)
                #T *= self.cooling

        if self.log:
            print('\n')
            print(self.change_stats)
        return AnnealResult(best_table, best_blocks, best_cost)
