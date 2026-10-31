from .classes import (
    ATB,
    Table,
    _Block,
    _Schedule,
)

MAX_PRIORITY = 10






def reset_ids(table: Table, atb:ATB, blocks:dict[int, _Block], start_from:int=1):
    sorted_blocks: list[_Block] = sorted(blocks.values(), key=lambda b: (b.day, b.start))

    old_to_new: dict[int, int] = {}
    new_blocks: dict[int, _Block] = {}

    for new_id, block in enumerate(sorted_blocks, start=start_from):
        old_id = block.id
        block.id = new_id
        old_to_new[old_id] = new_id
        new_blocks[new_id] = block

    for day_idx, day in enumerate(table):
        for slot_idx, slot in enumerate(day):
            if slot is not None:
                table[day_idx][slot_idx] = old_to_new[slot]


    for activity_id, block_ids in atb.items():
        atb[activity_id] = {old_to_new[block_id] for block_id in block_ids}

    blocks.clear()
    blocks.update(new_blocks)

    return table, blocks


def initial_table(db_activities, owner):
    from .classes import db_activities_to_engine_activities, engine_to_db_blocks
    from .scheduler import greedy_initial

    activities = db_activities_to_engine_activities(db_activities)

    dba_map = {a.id:a for a in db_activities}

    blocks, _, atb, _ = greedy_initial(activities)

    schedule = _Schedule(owner)
    schedule.owner = owner

    dbb_list = engine_to_db_blocks(schedule,blocks,atb,activities)
    for dbb in dbb_list:
        dbb.activity = dba_map[dbb.activity_id]
        dbb.group_name = dba_map[dbb.activity_id].group_name
        dbb.activity.blocks.add(dbb)
        dbb.colour = dba_map[dbb.activity_id].colour

    return dbb_list

def anneal_table(db_activities, owner):
    from .classes import db_activities_to_engine_activities, engine_to_db_blocks
    from .scheduler import greedy_initial, greedy_schedule

    activities = db_activities_to_engine_activities(db_activities)

    dba_map = {a.id:a for a in db_activities}

    blocks, table, atb, day_load = greedy_initial(activities)

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

    from app.engine.annealer import Annealer
    annealer = Annealer(
        table=table,
        activities=activities,
        blocks=blocks,
        atb=atb,
        day_load=day_load,
        scheduler=greedy_schedule
    )

    initial_cost = annealer.evaluator.total_cost

    best_table, best_blocks, best_cost = annealer.run()

    new_atb:dict[int, set[int]] = {}
    for id, block in best_blocks.items():
        new_atb.setdefault(block.activity_id, set()).add(id)

    best_table, best_blocks = reset_ids(best_table, new_atb, best_blocks)


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


    schedule = _Schedule(owner)
    schedule.owner = owner

    dbb_list = engine_to_db_blocks(schedule,blocks,atb,activities)
    for dbb in dbb_list:
        dbb.activity = dba_map[dbb.activity_id]
        dbb.group_name = dba_map[dbb.activity_id].group_name
        dbb.activity.blocks.add(dbb)
        dbb.colour = dba_map[dbb.activity_id].colour

    return dbb_list

__all__ = [
    'anneal_table',
    'initial_table'
]
