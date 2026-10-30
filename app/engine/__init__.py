from .classes import (
    ATB,
    Table,
    _Activity,
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

def test():
    # ai -generated activities
    activities = [
    # ------------------------------------------------------------------
    # 0 – Full‑time work (fixed 9 am‑5 pm Mon‑Fri, highest priority)
    # ------------------------------------------------------------------
    _Activity(
        name='Work',
        frequency=5,                    # one block per weekday
        even_spacing=False,
        min_weekly_minutes=2400,        # 40 h = 2400 min
        max_block_minutes=480,          # 8 h per block (480 min)
        min_start_minutes=9*60,         # 09:00 (irrelevant – already fixed)
        fixed=[                         # (day, start_min, length_min)
            (0, 9*60, 480),   # Monday
            (1, 9*60, 480),   # Tuesday
            (2, 9*60, 480),   # Wednesday
            (3, 9*60, 480),   # Thursday
            (4, 9*60, 480),   # Friday
        ],
        priority=5,
    ),

    # ------------------------------------------------------------------
    # 1 – Study (evenly spaced, night‑time, 3 × / week, priority 2)
    # ------------------------------------------------------------------
    _Activity(
        name='Study',
        frequency=7,
        even_spacing=True,
        min_weekly_minutes=720,         # 4 h total
        max_block_minutes=120,           # at most 2 h per session
        min_start_minutes=17*60,        # cannot start before 20:00
        fixed=[],
        priority=4,
    ),

    # ------------------------------------------------------------------
    # 2 – Piano lesson (fixed Thursday 18:00‑19:00, low priority)
    # ------------------------------------------------------------------
    _Activity(
        name='Piano',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=60,
        max_block_minutes=60,
        min_start_minutes=0,           # not used – fixed overrides it
        fixed=[(3, 18*60, 60)],         # Thursday 18:00‑19:00
        priority=3,
    ),

    # ------------------------------------------------------------------
    # 3 – Exercise (early‑morning, 2 × / week, priority 1)
    # ------------------------------------------------------------------
    _Activity(
        name='Exercise',
        frequency=2,
        even_spacing=False,
        min_weekly_minutes=120,         # 2 h total
        max_block_minutes=60,           # at most 1 h per session
        min_start_minutes=5*60,         # cannot start before 05:00
        fixed=[],
        priority=4,
    ),

    # ------------------------------------------------------------------
    # 4 – Yoga (morning, evenly spaced, 2 × / week, priority 2)
    # ------------------------------------------------------------------
    _Activity(
        name='Yoga',
        frequency=2,
        even_spacing=True,
        min_weekly_minutes=90,          # 1.5 h total
        max_block_minutes=60,           # ≤ 1 h per session
        min_start_minutes=6*60,        # cannot start before 06:00
        fixed=[],
        priority=3,
    ),

    # ------------------------------------------------------------------
    # 5 – Cooking (evenings, 3 × / week, priority 3)
    # ------------------------------------------------------------------
    _Activity(
        name='Cooking',
        frequency=3,
        even_spacing=False,
        min_weekly_minutes=180,         # 3 h total
        max_block_minutes=120,          # can be a 2‑hour dinner prep
        min_start_minutes=17*60,        # cannot start before 17:00
        fixed=[],
        priority=2,
    ),

    # ------------------------------------------------------------------
    # 6 – Grocery shopping (once a week, midday, priority 4)
    # ------------------------------------------------------------------
    _Activity(
        name='Groceries',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=60,
        max_block_minutes=60,
        min_start_minutes=10*60,        # cannot start before 10:00
        fixed=[],
        priority=2,
    ),

    # ------------------------------------------------------------------
    # 7 – Cleaning (once a week, morning, priority 4)
    # ------------------------------------------------------------------
    _Activity(
        name='Cleaning',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=120,
        max_block_minutes=120,
        min_start_minutes=9*60,
        fixed=[],
        priority=1,
    ),

    # ------------------------------------------------------------------
    # 8 – Laundry (once a week, early‑morning, priority 4)
    # ------------------------------------------------------------------
    _Activity(
        name='Laundry',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=60,
        max_block_minutes=60,
        min_start_minutes=9*60,
        fixed=[],
        priority=2,
    ),

    # ------------------------------------------------------------------
    # 9 – Reading (evenly spaced, night, 3 × / week, low priority)
    # ------------------------------------------------------------------
    _Activity(
        name='Reading',
        frequency=3,
        even_spacing=True,
        min_weekly_minutes=180,         # 3 h total
        max_block_minutes=90,           # at most 1.5 h per session
        min_start_minutes=20*60,        # cannot start before 20:00
        fixed=[],
        priority=1,
    ),

    # ------------------------------------------------------------------
    # 10 – Spanish (language learning, 2 × / week, evening, priority 5)
    # ------------------------------------------------------------------
    _Activity(
        name='Spanish',
        frequency=2,
        even_spacing=True,
        min_weekly_minutes=240,         # 2 h total
        max_block_minutes=60,           # ≤ 1 h per session
        min_start_minutes=19*60,        # cannot start before 19:00
        fixed=[],
        priority=1,
    ),


    # ------------------------------------------------------------------
    # 12 – Volunteer (once a week, mid‑morning, priority 2)
    # ------------------------------------------------------------------
    _Activity(
        name='Volunteer',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=180,          # 3 h total
        max_block_minutes=180,
        min_start_minutes=9*60,          # cannot start before 09:00
        fixed=[],
        priority=3,
    ),

    # ------------------------------------------------------------------
    # 13 – Meditation (short, 3 × / week, priority 5)
    # ------------------------------------------------------------------
    _Activity(
        name='Meditation',
        frequency=7,
        even_spacing=True,
        min_weekly_minutes=80,           # 30 min total
        max_block_minutes=30,            # each block ≤ 30 min
        min_start_minutes=6*60,          # cannot start before 06:00
        fixed=[],
        priority=1,
    ),

    # ------------------------------------------------------------------
    # 14 – Hiking (weekend‑only, long block, priority 3)
    # ------------------------------------------------------------------
    _Activity(
        name='Hiking',
        frequency=2,
        even_spacing=False,
        min_weekly_minutes=360,          # 4 h total
        max_block_minutes=240,           # can be a single 4‑hour block
        min_start_minutes=8*60,          # cannot start before 08:00
        fixed=[],           # Saturday 08:00‑12:00
        preferred_days=[5,6],
        priority=3,
    ),

    # ------------------------------------------------------------------
    # 15 – MealPrep (3 × / week, evening, priority 4)
    # ------------------------------------------------------------------
    _Activity(
        name='MealPrep',
        frequency=6,
        even_spacing=False,
        min_weekly_minutes=180,          # 3 h total
        max_block_minutes=60,            # each meal prep ≤ 1 h
        min_start_minutes=17*60,         # cannot start before 17:00
        fixed=[],
        priority=2,
    ),

    # ------------------------------------------------------------------
    # 16 – Homework (2 × / week, night, priority 2)
    # ------------------------------------------------------------------
    _Activity(
        name='Homework',
        frequency=5,
        even_spacing=False,
        min_weekly_minutes=260,          # 2 h total
        max_block_minutes=90,            # ≤ 1.5 h per session
        min_start_minutes=19*60,        # cannot start before 19:00
        fixed=[],
        priority=2,
    ),

    # ------------------------------------------------------------------
    # 17 – Language exchange (fixed Wednesday 20:00‑21:30, priority 3)
    # ------------------------------------------------------------------
    _Activity(
        name='LangExchange',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=90,
        max_block_minutes=90,
        min_start_minutes=0,
        fixed=[(2, 20*60, 90)],           # Wednesday 20:00‑21:30
        priority=2,
    ),

    # ------------------------------------------------------------------
    # 18 – Family time (2 × / week, evening, priority 2)
    # ------------------------------------------------------------------
    _Activity(
        name='FamilyTime',
        frequency=2,
        even_spacing=False,
        min_weekly_minutes=180,          # 3 h total
        max_block_minutes=120,           # ≤ 2 h per session
        min_start_minutes=18*60,        # cannot start before 18:00
        fixed=[],
        priority=3,
    ),

    # ------------------------------------------------------------------
    # 19 – Relax (optional low‑priority filler, 1 × / week, any time)
    # ------------------------------------------------------------------
    _Activity(
        name='Relax',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=60,           # just a half‑hour somewhere
        max_block_minutes=120,
        min_start_minutes=0,
        fixed=[],
        priority=1,                      # lowest priority – the algorithm will move it freely
    ),
    ]

    schedule = _Schedule()

    from app.engine.scheduler import greedy_initial, greedy_schedule

    blocks, table, activity_to_blocks, day_load = greedy_initial(activities)

    from app.engine.annealer import Annealer
    annealer = Annealer(
        table=table,
        activities=activities,
        blocks=blocks,
        atb=activity_to_blocks,
        day_load=day_load,
        scheduler=greedy_schedule
    )

    initial_cost = annealer.evaluator.total_cost
    print(initial_cost)

    print('\n\nRESULTS =======================================')
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