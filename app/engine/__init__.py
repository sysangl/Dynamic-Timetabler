from ..models import Block, Schedule
from .classes import (
    ATB,
    OverlapTable,
    _Block,
)

MAX_PRIORITY = 10


def reset_ids(table: OverlapTable, atb: ATB, blocks: dict[int, _Block], start_from: int = 1):
    sorted_blocks: list[_Block] = sorted(
        blocks.values(), key=lambda b: (b.day, b.start)
    )

    old_to_new: dict[int, int] = {}
    new_blocks: dict[int, _Block] = {}

    for new_id, block in enumerate(sorted_blocks, start=start_from):
        old_id = block.id
        block.id = new_id
        old_to_new[old_id] = new_id
        new_blocks[new_id] = block

    for day in table:
        for slot in day:
            old_ids = slot.copy()
            for id in old_ids:
                slot.remove(id)
                slot.add(old_to_new[id])


    for activity_id, block_ids in atb.items():
        atb[activity_id] = {old_to_new[block_id] for block_id in block_ids}

    blocks.clear()
    blocks.update(new_blocks)

    return table, blocks


def initial_table(db_schedule: Schedule):
    from .classes import (
        db_to_engine_activities,
        db_to_engine_schedule,
        engine_to_db_blocks,
    )
    from .scheduler import greedy_initial

    engine_schedule = db_to_engine_schedule(db_schedule)

    db_activities = db_schedule.activities
    activities = db_to_engine_activities(engine_schedule, db_activities)

    dba_map = {a.id: a for a in db_activities}

    blocks, _, atb, _ = greedy_initial(engine_schedule, activities)

    dbb_list = engine_to_db_blocks(engine_schedule, blocks, atb, activities)
    for dbb in dbb_list:
        dbb.activity = dba_map[dbb.activity_id]
        dbb.group_name = dba_map[dbb.activity_id].group_name
        dbb.activity.blocks.add(dbb)
        dbb.colour = dba_map[dbb.activity_id].colour

    return dbb_list


def anneal_table(db_schedule: Schedule, existing_blocks:list[Block]|None=None):
    from .classes import (
        db_blocks_to_engine_initial,
        db_to_engine_activities,
        db_to_engine_schedule,
        engine_to_db_blocks,
    )
    from .scheduler import greedy_initial, greedy_schedule

    engine_schedule = db_to_engine_schedule(db_schedule)

    db_activities = db_schedule.activities

    dba_map = {a.id: a for a in db_activities}
    activities = db_to_engine_activities(engine_schedule, db_activities)
    blocks, table, atb, day_load = greedy_initial(engine_schedule, activities)
    if existing_blocks:
    
        eblocks, etable, eatb, day_load, eactivities = db_blocks_to_engine_initial(engine_schedule, existing_blocks)
        for _bid, _b in eblocks.items():
            blocks[_bid] = _b
        for day in range(engine_schedule.SIZE):
            for row in range(engine_schedule.SLOTS_PER_DAY):
                table[day][row] = table[day][row].union(etable[day][row])
        for _a in eactivities:
            activities.append(_a)
        for _aid, _ab in eatb.items():
            atb[_aid] = _ab 
        for _a in activities:
            print(_a.id, _a.name)
        
        blocks, table, atb, day_load = greedy_initial(engine_schedule, activities, table,blocks,atb,day_load)

        print(blocks)
        print(table)
        print(atb)
        print(day_load)

    from app.engine.annealer import Annealer

    annealer = Annealer(
        engine_schedule,
        table=table,
        activities=activities,
        blocks=blocks,
        atb=atb,
        day_load=day_load,
        scheduler=greedy_schedule,
    )

    initial_cost = annealer.evaluator.total_cost

    best_table, best_blocks, best_cost = annealer.run()

    new_atb: dict[int, set[int]] = {}
    for id, block in best_blocks.items():
        new_atb.setdefault(block.activity_id, set()).add(id)

    best_table, best_blocks = reset_ids(best_table, new_atb, best_blocks)

    print("INFO ====================================")
    print(f"Init Cost:  {initial_cost}")
    print(f"Final Cost: {best_cost}")

    dbb_list = engine_to_db_blocks(engine_schedule, blocks, atb, activities)
    for dbb in dbb_list:
        if dbb.source != 'engine':
            continue
        if dbb.activity_id:
            dbb.activity = dba_map[dbb.activity_id]
            dbb.group_name = dba_map[dbb.activity_id].group_name
            dbb.activity.blocks.add(dbb)
            dbb.colour = dba_map[dbb.activity_id].colour

    return dbb_list


__all__ = ["anneal_table", "initial_table"]
