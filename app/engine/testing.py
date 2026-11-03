from ..engine import reset_ids
from .classes import _Activity, _Schedule


def test():
    from .classes import _Schedule
    from .scheduler import greedy_initial, greedy_schedule

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