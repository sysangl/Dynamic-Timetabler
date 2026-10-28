
if __name__ == "__main__":
    # ai -generated activities
    activities = [
        # ------------------------------------------------------------------
        #  0 – Full‑time work (fixed 9 am‑5 pm Mon‑Fri)
        # ------------------------------------------------------------------
        _Activity(
            name='Work',
            frequency=5,                     # Mon‑Fri
            even_spacing=False,
            min_weekly_minutes=2400,          # 40 h / week
            max_block_minutes=480,           # 8 h per day
            min_start_minutes=9*60,          # 09:00 (irrelevant – already fixed)
            fixed=[
                (0, 9*60, 480),   # Monday
                (1, 9*60, 480),   # Tuesday
                (2, 9*60, 480),   # Wednesday
                (3, 9*60, 480),   # Thursday
                (4, 9*60, 480),   # Friday
            ],
            priority=1,
        ),

        # ------------------------------------------------------------------
        #  1 – Study (evenly spaced, night‑time, 3×/week)
        # ------------------------------------------------------------------
        _Activity(
            name='Study',
            frequency=3,
            even_spacing=True,
            min_weekly_minutes=240,
            max_block_minutes=120,
            min_start_minutes=20*60,        # cannot start before 20:00
            fixed=[],
            priority=2,
        ),

        # ------------------------------------------------------------------
        #  2 – Piano lesson (fixed Thursday 18:00‑19:00)
        # ------------------------------------------------------------------
        _Activity(
            name='Piano',
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=60,
            max_block_minutes=60,
            min_start_minutes=0,            # not used – fixed overrides it
            fixed=[(3, 18*60, 60)],          # Thursday 18:00‑19:00
            priority=3,
        ),

        # ------------------------------------------------------------------
        #  3 – Exercise (early‑morning, 2×/week)
        # ------------------------------------------------------------------
        _Activity(
            name='Exercise',
            frequency=2,
            even_spacing=False,
            min_weekly_minutes=120,
            max_block_minutes=60,
            min_start_minutes=5*60,         # cannot start before 05:00
            fixed=[],
            priority=1,
        ),

        # ------------------------------------------------------------------
        #  4 – Yoga (morning, 2×/week, try to spread)
        # ------------------------------------------------------------------
        _Activity(
            name='Yoga',
            frequency=2,
            even_spacing=True,
            min_weekly_minutes=90,
            max_block_minutes=60,
            min_start_minutes=6*60,
            fixed=[],
            priority=2,
        ),

        # ------------------------------------------------------------------
        #  5 – Cooking (evenings, 3×/week)
        # ------------------------------------------------------------------
        _Activity(
            name='Cooking',
            frequency=3,
            even_spacing=False,
            min_weekly_minutes=180,
            max_block_minutes=120,
            min_start_minutes=17*60,
            fixed=[],
            priority=3,
        ),

        # ------------------------------------------------------------------
        #  6 – Grocery shopping (once a week, midday)
        # ------------------------------------------------------------------
        _Activity(
            name='Groceries',
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=60,
            max_block_minutes=60,
            min_start_minutes=10*60,
            fixed=[],
            priority=4,
        ),

        # ------------------------------------------------------------------
        #  7 – Cleaning (once a week, morning)
        # ------------------------------------------------------------------
        _Activity(
            name='Cleaning',
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=120,
            max_block_minutes=120,
            min_start_minutes=9*60,
            fixed=[],
            priority=4,
        ),

        # ------------------------------------------------------------------
        #  8 – Laundry (once a week, early‑morning)
        # ------------------------------------------------------------------
        _Activity(
            name='Laundry',
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=60,
            max_block_minutes=60,
            min_start_minutes=8*60,
            fixed=[],
            priority=4,
        ),

        # ------------------------------------------------------------------
        #  9 – Reading (evenly spaced, night, 3×/week)
        # ------------------------------------------------------------------
        _Activity(
            name='Reading',
            frequency=3,
            even_spacing=True,
            min_weekly_minutes=180,
            max_block_minutes=90,
            min_start_minutes=20*60,
            fixed=[],
            priority=5,
        ),

        # ------------------------------------------------------------------
        # 10 – Spanish (language learning, 2×/week, evening)
        # ------------------------------------------------------------------
        _Activity(
            name='Spanish',
            frequency=2,
            even_spacing=True,
            min_weekly_minutes=120,
            max_block_minutes=60,
            min_start_minutes=19*60,
            fixed=[],
            priority=5,
        ),
    ]

    blocks, table, activity_to_blocks, day_load = greedy_initial(activities)

    for day in range(SCHEDULE_SIZE):
        print(f'----- day {day}-------------------')
        day_blocks = [b for b in blocks.values() if b.day == day]
        day_blocks.sort(key=lambda b: b.start)

        for block in day_blocks:
            activity = next(a for a in activities if a.id == block.activity_id)
            start_mins = block.start * SLOT_SIZE
            end_mins = (block.start + block.length) * SLOT_SIZE
            start_hours = start_mins // 60
            start_mins = start_mins % 60
            end_hours = end_mins // 60
            end_mins = end_mins % 60
            print(
                f"  {activity.name:12s}  [{block.id:02d}]  "
                f"{start_hours:02d}:{start_mins:02d} - {end_hours:02d}:{end_mins:02d}  "
                f"(len={block.length} slots)"
            )

    evaluator = CostEvaluator(
        activities=activities,
        blocks=blocks,
        atb=activity_to_blocks,
        day_load=day_load
        )
    result_table, result_blocks, result_cost = simulated_annealing(
                                                                table,
                                                                activities,
                                                                activity_to_blocks,
                                                                blocks,
                                                                day_load,
                                                                evaluator
                                                            )

    print('RESULTS =======================================')

    for day in range(SCHEDULE_SIZE):
        print(f'----- day {day}-------------------')
        day_blocks = [b for b in result_blocks.values() if b.day == day]
        day_blocks.sort(key=lambda b: b.start)

        for block in day_blocks:
            activity = next(a for a in activities if a.id == block.activity_id)
            start_mins = block.start * SLOT_SIZE
            end_mins = (block.start + block.length) * SLOT_SIZE
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
    print(f'Cost {result_cost}')

    