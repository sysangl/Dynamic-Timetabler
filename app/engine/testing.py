from ..engine import reset_ids
from .classes import _Activity

activities = [
    # ------------------------------------------------------------------
    #  0 – Full‑time work (fixed 9 am‑5 pm Mon‑Fri, highest priority)
    # ------------------------------------------------------------------
    _Activity(
        name='Work',
        frequency=5,                               # one block per weekday
        even_spacing=False,
        min_weekly_minutes=2400,                 # 40 h = 2400 min
        min_block_minutes=480,                   # each block ≤ 8 h
        max_block_minutes=480,
        min_start_minutes=9 * 60,                # cannot start before 09:00
        fixed=[                                   # (day, start_min, length_min)
            (0, 9 * 60, 480),   # Monday
            (1, 9 * 60, 480),   # Tuesday
            (2, 9 * 60, 480),   # Wednesday
            (3, 9 * 60, 480),   # Thursday
            (4, 9 * 60, 480),   # Friday
        ],
        preferred_days=None,
        priority=1,
        db_id=101
    ),

    # ------------------------------------------------------------------
    #  1 – Study (evenly spaced, night‑time, 3 × / week, priority 2)
    # ------------------------------------------------------------------
    _Activity(
        name='Study',
        frequency=3,
        even_spacing=True,
        min_weekly_minutes=240,                 # 4 h total per week
        min_block_minutes=60,                   # you want at least 1 h per session
        max_block_minutes=120,                   # ≤ 2 h per session
        min_start_minutes=20 * 60,              # cannot start before 20:00
        fixed=[],
        preferred_days=None,
        priority=2,
        db_id=102
    ),

    # ------------------------------------------------------------------
    #  2 – Piano lesson (fixed Thursday 18:00‑19:00, low priority)
    # ------------------------------------------------------------------
    _Activity(
        name='Piano',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=60,
        min_block_minutes=60,
        max_block_minutes=60,
        min_start_minutes=0,                     # not used – fixed overrides it
        fixed=[(3, 18 * 60, 60)],                 # Thursday 18:00‑19:00
        preferred_days=None,
        priority=3,
        db_id=103
    ),

    # ------------------------------------------------------------------
    #  3 – Exercise (early‑morning, 2 × / week, priority 1)
    # ------------------------------------------------------------------
    _Activity(
        name='Exercise',
        frequency=2,
        even_spacing=False,
        min_weekly_minutes=120,                  # 2 h total per week
        min_block_minutes=30,                   # at least 30 min per session
        max_block_minutes=60,                   # ≤ 1 h per session
        min_start_minutes=5 * 60,               # cannot start before 05:00
        fixed=[],
        preferred_days=None,
        priority=1,
        db_id=104
    ),

    # ------------------------------------------------------------------
    #  4 – Yoga (morning, evenly spaced, 2 × / week, priority 2)
    # ------------------------------------------------------------------
    _Activity(
        name='Yoga',
        frequency=2,
        even_spacing=True,
        min_weekly_minutes=90,                 # 1.5 h total per week
        min_block_minutes=45,                  # at least 45 min per session
        max_block_minutes=60,                   # ≤ 1 h per session
        min_start_minutes=6 * 60,              # cannot start before 06:00
        fixed=[],
        preferred_days=None,
        priority=2,
        db_id=105
    ),

    # ------------------------------------------------------------------
    #  5 – Cooking (evenings, 3 × / week, priority 3)
    # ------------------------------------------------------------------
    _Activity(
        name='Cooking',
        frequency=3,
        even_spacing=False,
        min_weekly_minutes=180,                 # 3 h total per week
        min_block_minutes=30,                  # at least 30 min per session
        max_block_minutes=120,                  # you may have a long prep night
        min_start_minutes=17 * 60,              # cannot start before 17:00
        fixed=[],
        preferred_days=None,
        priority=3,
        db_id=106
    ),

    # ------------------------------------------------------------------
    #  6 – Grocery shopping (once a week, midday, priority 4)
    # ------------------------------------------------------------------
    _Activity(
        name='Groceries',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=60,
        min_block_minutes=30,
        max_block_minutes=60,
        min_start_minutes=10 * 60,              # cannot start before 10:00
        fixed=[],
        preferred_days=[6],                     # Saturday is preferred
        priority=4,
        db_id=107
    ),

    # ------------------------------------------------------------------
    #  7 – Cleaning (once a week, morning, priority 4)
    # ------------------------------------------------------------------
    _Activity(
        name='Cleaning',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=120,
        min_block_minutes=60,
        max_block_minutes=120,
        min_start_minutes=9 * 60,
        fixed=[],
        preferred_days=[0],                     # Monday is preferred
        priority=4,
        db_id=108
    ),

    # ------------------------------------------------------------------
    #  8 – Laundry (once a week, early‑morning, priority 4)
    # ------------------------------------------------------------------
    _Activity(
        name='Laundry',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=60,
        min_block_minutes=30,
        max_block_minutes=60,
        min_start_minutes=8 * 60,
        fixed=[],
        preferred_days=[2],                     # Wednesday is preferred
        priority=4,
        db_id=109
    ),

    # ------------------------------------------------------------------
    #  9 – Reading (evenly spaced, night, 3 × / week, low priority)
    # ------------------------------------------------------------------
    _Activity(
        name='Reading',
        frequency=3,
        even_spacing=True,
        min_weekly_minutes=180,                 # 3 h total per week
        min_block_minutes=30,
        max_block_minutes=90,
        min_start_minutes=20 * 60,             # cannot start before 20:00
        fixed=[],
        preferred_days=None,
        priority=5,
        db_id=110
    ),

    # ------------------------------------------------------------------
    # 10 – Spanish (language learning, 2 × / week, evening, priority 5)
    # ------------------------------------------------------------------
    _Activity(
        name='Spanish',
        frequency=2,
        even_spacing=True,
        min_weekly_minutes=120,
        min_block_minutes=30,
        max_block_minutes=60,
        min_start_minutes=19 * 60,             # cannot start before 19:00
        fixed=[],
        preferred_days=None,
        priority=5,
        db_id=111
    ),

    # ------------------------------------------------------------------
    # 11 – Volunteer (once a week, mid‑morning, priority 2)
    # ------------------------------------------------------------------
    _Activity(
        name='Volunteer',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=180,                  # 3 h total per week
        min_block_minutes=60,
        max_block_minutes=180,
        min_start_minutes=9 * 60,
        fixed=[],
        preferred_days=[4],                      # Thursday is preferred
        priority=2,
        db_id=112
    ),

    # ------------------------------------------------------------------
    # 12 – Meditation (short, 3 × / week, any time, priority 5)
    # ------------------------------------------------------------------
    _Activity(
        name='Meditation',
        frequency=3,
        even_spacing=False,
        min_weekly_minutes=30,                  # 30 min total per week
        min_block_minutes=10,
        max_block_minutes=30,
        min_start_minutes=6 * 60,               # cannot start before 06:00
        fixed=[],
        preferred_days=None,
        priority=5,
        db_id=113
    ),

    # ------------------------------------------------------------------
    # 13 – Hiking (weekend‑only, long block, priority 3)
    # ------------------------------------------------------------------
    _Activity(
        name='Hiking',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=240,                 # 4 h total per week
        min_block_minutes=120,
        max_block_minutes=240,
        min_start_minutes=8 * 60,
        fixed=[(5, 8 * 60, 240)],                # Saturday 08:00‑12:00
        preferred_days=None,
        priority=3,
        db_id=114
    ),

    # ------------------------------------------------------------------
    # 14 – MealPrep (3 × / week, evening, priority 4)
    # ------------------------------------------------------------------
    _Activity(
        name='MealPrep',
        frequency=3,
        even_spacing=False,
        min_weekly_minutes=180,
        min_block_minutes=30,
        max_block_minutes=60,
        min_start_minutes=17 * 60,
        fixed=[],
        preferred_days=None,
        priority=4,
        db_id=115
    ),

    # ------------------------------------------------------------------
    # 15 – Homework (2 × / week, night, priority 2)
    # ------------------------------------------------------------------
    _Activity(
        name='Homework',
        frequency=2,
        even_spacing=False,
        min_weekly_minutes=120,
        min_block_minutes=30,
        max_block_minutes=90,
        min_start_minutes=19 * 60,
        fixed=[],
        preferred_days=None,
        priority=2,
        db_id=116
    ),

    # ------------------------------------------------------------------
    # 16 – Language exchange (fixed Wed 20:00‑21:30, priority 3)
    # ------------------------------------------------------------------
    _Activity(
        name='LangExchange',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=90,
        min_block_minutes=90,
        max_block_minutes=90,
        min_start_minutes=0,
        fixed=[(2, 20 * 60, 90)],               # Wednesday 20:00‑21:30
        preferred_days=None,
        priority=3,
        db_id=117
    ),

    # ------------------------------------------------------------------
    # 17 – Family time (2 × / week, evening, priority 2)
    # ------------------------------------------------------------------
    _Activity(
        name='FamilyTime',
        frequency=2,
        even_spacing=False,
        min_weekly_minutes=180,
        min_block_minutes=60,
        max_block_minutes=120,
        min_start_minutes=18 * 60,
        fixed=[],
        preferred_days=None,
        priority=2,
        db_id=118
    ),

    # ------------------------------------------------------------------
    # 18 – Relax (optional filler, 1 × / week, any time, lowest priority)
    # ------------------------------------------------------------------
    _Activity(
        name='Relax',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=30,
        min_block_minutes=30,
        max_block_minutes=30,
        min_start_minutes=0,
        fixed=[],
        preferred_days=None,
        priority=6,            # lowest priority – the algorithm will move it freely
        db_id=119
    ),

    # ------------------------------------------------------------------
    # 19 – Team meeting (fixed Monday 12:00‑13:00, high priority)
    # ------------------------------------------------------------------
    _Activity(
        name='TeamMeeting',
        frequency=1,
        even_spacing=False,
        min_weekly_minutes=60,
        min_block_minutes=60,
        max_block_minutes=60,
        min_start_minutes=0,
        fixed=[],               # Monday 12:00‑13:00
        preferred_days=None,
        priority=1,
        db_id=120
    ),
]


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