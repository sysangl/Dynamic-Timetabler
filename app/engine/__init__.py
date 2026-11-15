from ..models import Block, Schedule
from .classes import AnnealResult, ATB, OverlapTable, _Activity, _Block, _Schedule

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

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


def initial_table(schedule: Schedule, existing_blocks: list[Block]| None=None):
    from .classes import (
        db_blocks_to_engine_initial,
        db_to_engine_activities,
        db_to_engine_schedule,
        engine_to_db_blocks,
    )
    from .scheduler import greedy_initial

    engine_schedule = db_to_engine_schedule(schedule)

    db_activities = schedule.activities

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
            print(f'{_aid} = {_ab}')
        
        blocks, table, atb, day_load = greedy_initial(engine_schedule, activities, table,blocks,atb,day_load)

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

def anneal_table(schedule: Schedule | _Schedule, existing_blocks:list[Block]|None=None, activities:list[_Activity]|None=None, parallel_count = 0) -> list[Block]:
    from .classes import (
        db_blocks_to_engine_initial,
        db_to_engine_activities,
        db_to_engine_schedule,
        engine_to_db_blocks,
    )
    from .scheduler import greedy_initial, greedy_schedule

    dba_map={}
    if type(schedule) == Schedule:
        engine_schedule = db_to_engine_schedule(schedule)
        db_activities = schedule.activities
        dba_map = {a.id: a for a in db_activities}
        activities = db_to_engine_activities(engine_schedule, db_activities)
    else:
        if not activities:
            print('Activities are required to generate from a _Schedule')
            return []
        assert type(schedule) == _Schedule 
        engine_schedule = schedule

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
            print(f'{_aid} = {_ab}')
        
        blocks, table, atb, day_load = greedy_initial(engine_schedule, activities, table,blocks,atb,day_load)

    for _aid, _ab in atb.items():
        atb[_aid] = _ab 
        print(f'{_aid} = {_ab}')



    print("\n\nINITIAL =======================================")
    for day in range(engine_schedule.SIZE):
        print(f"----- day {day}-------------------")
        day_blocks = [b for b in blocks.values() if b.day == day]
        day_blocks.sort(key=lambda b: b.start)

        for block in day_blocks:
            activity = next(a for a in activities if a.id == block.activity_id)
            start_mins = block.start * engine_schedule.SLOT_SIZE
            end_mins = (block.start + block.length) * engine_schedule.SLOT_SIZE
            start_hours = start_mins // 60
            start_mins = start_mins % 60
            end_hours = end_mins // 60
            end_mins = end_mins % 60
            print(
                f"  {activity.name:12s}  [{block.id:02d}]  "
                f"{start_hours:02d}:{start_mins:02d} - {end_hours:02d}:{end_mins:02d}  "
                f"(len={block.length} slots)"
            )


    from app.engine.annealer import Annealer



    
    annealer = Annealer(
        engine_schedule,
        table=table,
        activities=activities,
        blocks=blocks,
        atb=atb,
        day_load=day_load,
        scheduler=greedy_schedule,
        log=True
    )
    initial_cost = annealer.evaluator.total_cost
    if parallel_count == 0:
        result = annealer.run()

    else:
        import copy
        def parallel_anneal(run_id):
            print(f'Anneal {run_id}')
            ptable = copy.deepcopy(table)
            pblocks = copy.deepcopy(blocks)
            patb = copy.deepcopy(atb)
            pday_load = copy.deepcopy(day_load)
            annealer = Annealer(
                engine_schedule,
                table=ptable,
                activities=activities,
                blocks=pblocks,
                atb=patb,
                day_load=pday_load,
                scheduler=greedy_schedule
            )
            return annealer.run()

        with ThreadPoolExecutor() as executor:
            results = executor.map(parallel_anneal, range(parallel_count))

        import math
        best_result = AnnealResult([],{},math.inf)

        for result in results:
            print(result)
            if result.cost < best_result.cost:
                best_result = result

        result = best_result

    best_blocks = result.blocks
    best_table = result.table
    best_cost = result.cost


    print('best blocks after annealer ---------------')
    for bid, b in best_blocks.items():
        print(f'{bid}:{b.activity_id}')

    new_atb: dict[int, set[int]] = {}
    for id, block in best_blocks.items():
        new_atb.setdefault(block.activity_id, set()).add(id)

    best_table, best_blocks = reset_ids(best_table, new_atb, best_blocks)

    print("\nOPTIMISED =======================================")
    for day in range(engine_schedule.SIZE):
        print(f"----- day {day}-------------------")
        day_blocks = [b for b in best_blocks.values() if b.day == day]
        day_blocks.sort(key=lambda b: b.start)
        total_slots = 0

        for block in day_blocks:
            activity = next(a for a in activities if a.id == block.activity_id)
            start_mins = block.start * engine_schedule.SLOT_SIZE
            end_mins = (block.start + block.length) * engine_schedule.SLOT_SIZE
            start_hours = start_mins // 60
            start_mins = start_mins % 60
            end_hours = end_mins // 60
            end_mins = end_mins % 60
            print(
                f"  {activity.name:12s}  [{block.id:02d}]  "
                f"{start_hours:02d}:{start_mins:02d} - {end_hours:02d}:{end_mins:02d}  "
                f"(len={block.length} slots)"
            )
            total_slots += block.length
        print(f"Total Slots : {total_slots} ({total_slots * engine_schedule.SLOT_SIZE} minutes)")



    print("INFO ====================================")
    print(f"Init Cost:  {initial_cost}")
    print(f"Final Cost: {best_cost}")

    dbb_list = engine_to_db_blocks(engine_schedule, best_blocks, new_atb, activities)
    if type(schedule) == Schedule:
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
