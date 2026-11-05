import datetime
import random
import uuid

from ..engine import reset_ids
from ..models.user import User
from .classes import _Activity, _Schedule


def make_db_id():
    return uuid.uuid4()

def make_fixed_block(day, starth, startm, lenh, lenm):
    return (day, starth*60+startm, lenh*60+lenm)

def random_preferred_days(n):
    return random.choices([0,1,2,3,4,5,6],k=2)

def test(max_iter=None):
    from .scheduler import greedy_initial, greedy_schedule

    schedule = _Schedule(
        uuid.UUID('75bab872-2284-41ec-bbdc-baeabea8921a'),
        owner=User('Testing'),
        start_date=datetime.datetime.now().date()
        )

    activities = [

        # ------------------------------------------------------------------
        #  0 – Full‑time work (fixed 9 am‑5 pm Mon‑Fri, highest priority)
        # ------------------------------------------------------------------
        _Activity(
            name='Work',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=5,
            even_spacing=False,
            min_weekly_minutes=2400,               # 40 h
            min_block_minutes=480,                 # 8 h per day
            max_block_minutes=480,
            min_start_minutes=9 * 60,
            fixed=[
                (0, 9 * 60, 480),   # Monday
                (1, 9 * 60, 480),   # Tuesday
                (2, 9 * 60, 480),   # Wednesday
                (3, 9 * 60, 480),   # Thursday
                (4, 9 * 60, 480),   # Friday
            ],
            preferred_days=None,
            priority=1,
        ),

        # ------------------------------------------------------------------
        #  1 – Study (evenly spaced, night‑time, 3 × / week)
        # ------------------------------------------------------------------
        _Activity(
            name='Study',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=3,
            even_spacing=True,
            min_weekly_minutes=240,                # 4 h total
            min_block_minutes=60,
            max_block_minutes=120,
            min_start_minutes=20 * 60,             # cannot start before 20:00
            fixed=None,
            preferred_days=None,
            priority=2,
        ),

        # ------------------------------------------------------------------
        #  2 – Piano lesson (fixed Thursday 18:00‑19:00)
        # ------------------------------------------------------------------
        _Activity(
            name='Piano',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=60,
            min_block_minutes=60,
            max_block_minutes=60,
            min_start_minutes=0,
            fixed=[make_fixed_block(3, 18, 0, 1, 0)],  # Thursday 18:00‑19:00
            preferred_days=None,
            priority=3,
        ),

        # ------------------------------------------------------------------
        #  3 – Exercise (early‑morning, 2 × / week)
        # ------------------------------------------------------------------
        _Activity(
            name='Exercise',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=2,
            even_spacing=False,
            min_weekly_minutes=120,
            min_block_minutes=30,
            max_block_minutes=60,
            min_start_minutes=5 * 60,              # cannot start before 05:00
            fixed=None,
            preferred_days=None,
            priority=1,
        ),

        # ------------------------------------------------------------------
        #  4 – Yoga (morning, evenly spaced, 2 × / week)
        # ------------------------------------------------------------------
        _Activity(
            name='Yoga',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=2,
            even_spacing=True,
            min_weekly_minutes=90,
            min_block_minutes=45,
            max_block_minutes=60,
            min_start_minutes=6 * 60,
            fixed=None,
            preferred_days=None,
            priority=2,
        ),

        # ------------------------------------------------------------------
        #  5 – Cooking (evenings, 3 × / week)
        # ------------------------------------------------------------------
        _Activity(
            name='Cooking',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=3,
            even_spacing=False,
            min_weekly_minutes=180,
            min_block_minutes=30,
            max_block_minutes=120,
            min_start_minutes=17 * 60,
            fixed=None,
            preferred_days=None,
            priority=3,
        ),

        # ------------------------------------------------------------------
        #  6 – Grocery shopping (once a week, midday)
        # ------------------------------------------------------------------
        _Activity(
            name='Groceries',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=60,
            min_block_minutes=30,
            max_block_minutes=60,
            min_start_minutes=10 * 60,
            fixed=None,
            preferred_days=[5, 6],                # prefer weekend
            priority=4,
        ),

        # ------------------------------------------------------------------
        #  7 – Cleaning (once a week, morning)
        # ------------------------------------------------------------------
        _Activity(
            name='Cleaning',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=120,
            min_block_minutes=60,
            max_block_minutes=120,
            min_start_minutes=9 * 60,
            fixed=None,
            preferred_days=[0],                   # prefer Monday
            priority=4,
        ),

        # ------------------------------------------------------------------
        #  8 – Laundry (once a week, early‑morning)
        # ------------------------------------------------------------------
        _Activity(
            name='Laundry',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=60,
            min_block_minutes=30,
            max_block_minutes=60,
            min_start_minutes=8 * 60,
            fixed=None,
            preferred_days=[2],                    # prefer Wednesday
            priority=4,
        ),

        # ------------------------------------------------------------------
        #  9 – Reading (evenly spaced, night, 3 × / week)
        # ------------------------------------------------------------------
        _Activity(
            name='Reading',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=3,
            even_spacing=True,
            min_weekly_minutes=180,
            min_block_minutes=30,
            max_block_minutes=90,
            min_start_minutes=20 * 60,
            fixed=None,
            preferred_days=None,
            priority=5,
        ),

        # ------------------------------------------------------------------
        # 10 – Spanish (language learning, 2 × / week, evening)
        # ------------------------------------------------------------------
        _Activity(
            name='Spanish',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=2,
            even_spacing=True,
            min_weekly_minutes=120,
            min_block_minutes=30,
            max_block_minutes=60,
            min_start_minutes=19 * 60,
            fixed=None,
            preferred_days=None,
            priority=5,
        ),

        # ------------------------------------------------------------------
        # 11 – Volunteer (once a week, mid‑morning)
        # ------------------------------------------------------------------
        _Activity(
            name='Volunteer',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=180,
            min_block_minutes=60,
            max_block_minutes=180,
            min_start_minutes=9 * 60,
            fixed=None,
            preferred_days=[4],                   # prefer Thursday
            priority=2,
        ),

        # ------------------------------------------------------------------
        # 12 – Meditation (short, 3 × / week, any time)
        # ------------------------------------------------------------------
        _Activity(
            name='Meditation',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=3,
            even_spacing=False,
            min_weekly_minutes=30,
            min_block_minutes=10,
            max_block_minutes=30,
            min_start_minutes=6 * 60,
            fixed=None,
            preferred_days=None,
            priority=5,
        ),

        # ------------------------------------------------------------------
        # 13 – Hiking (weekend‑only, long block)
        # ------------------------------------------------------------------
        _Activity(
            name='Hiking',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=240,
            min_block_minutes=120,
            max_block_minutes=240,
            min_start_minutes=8 * 60,
            fixed=[make_fixed_block(5, 8, 0, 4, 0)],   # Saturday 08:00‑12:00
            preferred_days=None,
            priority=3,
        ),

        # ------------------------------------------------------------------
        # 14 – MealPrep (3 × / week, evening)
        # ------------------------------------------------------------------
        _Activity(
            name='MealPrep',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=3,
            even_spacing=False,
            min_weekly_minutes=180,
            min_block_minutes=30,
            max_block_minutes=60,
            min_start_minutes=17 * 60,
            fixed=None,
            preferred_days=None,
            priority=4,
        ),

        # ------------------------------------------------------------------
        # 15 – Homework (2 × / week, night)
        # ------------------------------------------------------------------
        _Activity(
            name='Homework',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=2,
            even_spacing=False,
            min_weekly_minutes=120,
            min_block_minutes=30,
            max_block_minutes=90,
            min_start_minutes=19 * 60,
            fixed=None,
            preferred_days=None,
            priority=2,
        ),

        # ------------------------------------------------------------------
        # 16 – Language exchange (fixed Wednesday 20:00‑21:30)
        # ------------------------------------------------------------------
        _Activity(
            name='LangExchange',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=90,
            min_block_minutes=90,
            max_block_minutes=90,
            min_start_minutes=0,
            fixed=None,   # Wed 20:00‑21:30
            preferred_days=None,
            priority=3,
        ),

        # ------------------------------------------------------------------
        # 17 – Family time (2 × / week, evening)
        # ------------------------------------------------------------------
        _Activity(
            name='FamilyTime',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=2,
            even_spacing=False,
            min_weekly_minutes=180,
            min_block_minutes=60,
            max_block_minutes=120,
            min_start_minutes=18 * 60,
            fixed=None,
            preferred_days=None,
            priority=2,
        ),

        # ------------------------------------------------------------------
        # 18 – Relax (optional filler, 1 × / week, any time, lowest priority)
        # ------------------------------------------------------------------
        _Activity(
            name='Relax',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=30,
            min_block_minutes=30,
            max_block_minutes=30,
            min_start_minutes=0,
            fixed=None,
            preferred_days=None,
            priority=6,       # lowest priority – will be moved freely by SA
        ),

        # ------------------------------------------------------------------
        # 19 – Team meeting (fixed Monday 12:00‑13:00)
        # ------------------------------------------------------------------
        _Activity(
            name='TeamMeeting',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=60,
            min_block_minutes=60,
            max_block_minutes=60,
            min_start_minutes=0,
            fixed=[],   # Monday 12:00‑13:00
            preferred_days=None,
            priority=1,
        ),

        # ------------------------------------------------------------------
        # 20 – Swimming (twice a week, morning, priority 3)
        # ------------------------------------------------------------------
        _Activity(
            name='Swimming',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=2,
            even_spacing=False,
            min_weekly_minutes=120,
            min_block_minutes=30,
            max_block_minutes=90,
            min_start_minutes=7 * 60,
            fixed=None,
            preferred_days=random_preferred_days(2),
            priority=3,
        ),

        # ------------------------------------------------------------------
        # 21 – Piano practice (not the lesson – short daily practice)
        # ------------------------------------------------------------------
        _Activity(
            name='PianoPractice',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=5,
            even_spacing=True,
            min_weekly_minutes=150,
            min_block_minutes=20,
            max_block_minutes=40,
            min_start_minutes=17 * 60,
            fixed=None,
            preferred_days=None,
            priority=4,
        ),

        # ------------------------------------------------------------------
        # 22 – Walk (daily short walk, very low priority)
        # ------------------------------------------------------------------
        _Activity(
            name='Walk',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=7,
            even_spacing=True,
            min_weekly_minutes=70,
            min_block_minutes=10,
            max_block_minutes=20,
            min_start_minutes=6 * 60,
            fixed=None,
            preferred_days=None,
            priority=7,       # even lower than “Relax”
        ),

        # ------------------------------------------------------------------
        # 23 – Gardening (twice a week, late afternoon)
        # ------------------------------------------------------------------
        _Activity(
            name='Gardening',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=2,
            even_spacing=False,
            min_weekly_minutes=120,
            min_block_minutes=45,
            max_block_minutes=90,
            min_start_minutes=16 * 60,
            fixed=None,
            preferred_days=random_preferred_days(2),
            priority=3,
        ),

        # ------------------------------------------------------------------
        # 24 – Doctor appointment (single fixed block, high priority)
        # ------------------------------------------------------------------
        _Activity(
            name='Doctor',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=60,
            min_block_minutes=60,
            max_block_minutes=60,
            min_start_minutes=0,
            fixed=[make_fixed_block(1, 18, 0, 1, 0)],   # Tuesday 14:00‑15:00
            preferred_days=None,
            priority=1,
        ),

        # ------------------------------------------------------------------
        # 25 – Music rehearsal (fixed Saturday afternoon)
        # ------------------------------------------------------------------
        _Activity(
            name='MusicRehearsal',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=180,
            min_block_minutes=180,
            max_block_minutes=180,
            min_start_minutes=0,
            fixed=[make_fixed_block(5, 15, 0, 3, 0)],   # Sat 15:00‑18:00
            preferred_days=None,
            priority=2,
        ),

        # ------------------------------------------------------------------
        # 26 – Language class (fixed Thursday 10:00‑11:30)
        # ------------------------------------------------------------------
        _Activity(
            name='LanguageClass',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=90,
            min_block_minutes=90,
            max_block_minutes=90,
            min_start_minutes=0,
            fixed=[make_fixed_block(3, 20, 0, 1, 30)],  # Thu 10:00‑11:30
            preferred_days=None,
            priority=2,
        ),

        # ------------------------------------------------------------------
        # 27 – Coding practice (3 × / week, evening)
        # ------------------------------------------------------------------
        _Activity(
            name='Coding',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=3,
            even_spacing=True,
            min_weekly_minutes=180,
            min_block_minutes=30,
            max_block_minutes=90,
            min_start_minutes=18 * 60,
            fixed=None,
            preferred_days=None,
            priority=4,
        ),

        # ------------------------------------------------------------------
        # 28 – Therapy session (once a week, mid‑day)
        # ------------------------------------------------------------------
        _Activity(
            name='Therapy',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=60,
            min_block_minutes=60,
            max_block_minutes=60,
            min_start_minutes=0,
            fixed=[make_fixed_block(4, 21, 0, 1, 0)],   # Friday 13:00‑14:00
            preferred_days=None,
            priority=1,
        ),

        # ------------------------------------------------------------------
        # 29 – Film night (once a week, weekend, long block)
        # ------------------------------------------------------------------
        _Activity(
            name='FilmNight',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=180,
            min_block_minutes=120,
            max_block_minutes=180,
            min_start_minutes=20 * 60,
            fixed=[make_fixed_block(6, 20, 0, 3, 0)],   # Sunday 20:00‑23:00
            preferred_days=None,
            priority=3,
        ),

        # ------------------------------------------------------------------
        # 30 – Soccer practice (fixed Wednesday evening)
        # ------------------------------------------------------------------
        _Activity(
            name='Soccer',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=1,
            even_spacing=False,
            min_weekly_minutes=120,
            min_block_minutes=120,
            max_block_minutes=120,
            min_start_minutes=0,
            fixed=[make_fixed_block(2, 18, 0, 2, 0)],   # Wed 18:00‑20:00
            preferred_days=None,
            priority=2,
        ),

        # ------------------------------------------------------------------
        # 31 – Coffee break (tiny filler, 5 × / week, any time)
        # ------------------------------------------------------------------
        _Activity(
            name='CoffeeBreak',
            db_id=make_db_id(),
            schedule=schedule,
            frequency=5,
            even_spacing=False,
            min_weekly_minutes=30,
            min_block_minutes=5,
            max_block_minutes=10,
            min_start_minutes=0,
            fixed=None,
            preferred_days=None,
            priority=8,
        ),
    ]


    blocks, table, atb, day_load = greedy_initial(schedule,activities)

    print("\n\nINITIAL =======================================")
    for day in range(schedule.SIZE):
        print(f"----- day {day}-------------------")
        day_blocks = [b for b in blocks.values() if b.day == day]
        day_blocks.sort(key=lambda b: b.start)

        for block in day_blocks:
            activity = next(a for a in activities if a.id == block.activity_id)
            start_mins = block.start * schedule.SLOT_SIZE
            end_mins = (block.start + block.length) * schedule.SLOT_SIZE
            start_hours = start_mins // 60
            start_mins = start_mins % 60
            end_hours = end_mins // 60
            end_mins = end_mins % 60
            print(
                f"  {activity.name:12s}  [{block.id:02d}]  "
                f"{start_hours:02d}:{start_mins:02d} - {end_hours:02d}:{end_mins:02d}  "
                f"(len={block.length} slots)"
            )

    print("\n\nOptimised ======================================")

    from app.engine.annealer import Annealer

    annealer = Annealer(
        schedule=schedule,
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

    for day in range(schedule.SIZE):
        print(f"----- day {day}-------------------")
        day_blocks = [b for b in best_blocks.values() if b.day == day]
        day_blocks.sort(key=lambda b: b.start)

        for block in day_blocks:
            activity = next(a for a in activities if a.id == block.activity_id)
            start_mins = block.start * schedule.SLOT_SIZE
            end_mins = (block.start + block.length) * schedule.SLOT_SIZE
            start_hours = start_mins // 60
            start_mins = start_mins % 60
            end_hours = end_mins // 60
            end_mins = end_mins % 60
            print(
                f"  {activity.name:12s}  [{block.id:02d}]  "
                f"{start_hours:02d}:{start_mins:02d} - {end_hours:02d}:{end_mins:02d}  "
                f"(len={block.length} slots)"
            )

    print("INFO ====================================")
    print(f"Init Cost:  {initial_cost}")
    print(f"Final Cost: {best_cost}")
