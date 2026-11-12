import random

from .classes import ATB, OverlapTable, _Activity, _Block, _Schedule


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def clear_block(table: OverlapTable, b: _Block):
    for slot in range(b.start,min( b.start + b.length, len(table[b.day]))):
        table[b.day][slot].remove(b.id)


def find_free_slots(
    day: int, required_size: int, table: OverlapTable, start_from: int = 0
) -> int | None:
    start = 0
    free_slots = 0
    row = table[day]
    for slot in range(start_from, len(row)):
        if len(row[slot]) == 0:
            if free_slots == 0:
                start = slot
            free_slots += 1
            if free_slots >= required_size:
                return start
        else:
            free_slots = 0
    return None


def allocate_lengths(needed: int, sessions: int, max_len: int) -> list[int]:
    base_len = max(1, min(max_len, needed // sessions))
    lengths = [base_len] * sessions
    remaining = needed - base_len * sessions

    i = 0
    while remaining > 0:
        if lengths[i] < max_len:
            lengths[i] += 1
            remaining -= 1
        i = (i + 1) % sessions
        if i == 0 and all(l == max_len for l in lengths):
            break
    return lengths


def can_place(schedule: _Schedule, table: OverlapTable, b: _Block):
    for slot in range(b.start, b.start + b.length):
        try:
            if slot >= schedule.SLOTS_PER_DAY or not (0 <= b.day < schedule.SIZE):
                return False
            if not table[b.day][slot].issubset({b.id}):
                return False
        except IndexError:
            print(f"can_place failed : slot {slot}")
            return False
    return True


def place_block(table: OverlapTable, b: _Block):
    for slot in range(b.start,min( b.start + b.length, len(table[b.day]))):
        table[b.day][slot].add(b.id)


def greedy_schedule(
    activity: _Activity,
    table: OverlapTable,
    blocks: dict[int, _Block],
    activity_to_blocks: ATB,
    day_load: list[int],
):
    needed_sessions = max(activity.frequency, 1)

    total_needed = max(activity.min_weekly_slots, needed_sessions)

    lengths = allocate_lengths(total_needed, needed_sessions, activity.max_block_slots)
    used_days: set[int] = set()

    if activity.even_spacing:
        target_days = [
            min(
                max(0, round(i * activity.schedule.SIZE / needed_sessions)),
                activity.schedule.SIZE - 1,
            )
            for i in range(needed_sessions)
        ]
    else:
        target_days = [None] * needed_sessions

    for idx, block_length in enumerate(lengths):
        candidate_days: list[int] = []
        if activity.even_spacing:
            ideal = target_days[idx]
            offsets = []
            for day in range(activity.schedule.SIZE):
                offsets.append(day)
                offsets.append(-day)
            for offset in offsets:
                day = ideal + offset
                if 0 <= day < activity.schedule.SIZE and day not in used_days:
                    candidate_days.append(day)
            if not candidate_days:
                candidate_days = list(range(activity.schedule.SIZE))
        elif len(activity.preferred_days) > 0:
            candidate_days = activity.preferred_days

        else:
            activities_per_day = [
                (
                    day,
                    sum(
                        1
                        for id in activity_to_blocks[activity.id]
                        if blocks[id].day == day
                    ),
                    day_load[day],
                )
                for day in range(activity.schedule.SIZE)
            ]
            activities_per_day.sort(key=lambda x: (x[1], x[2]))
            candidate_days = [day for day, _, _ in activities_per_day]

        placed = False

        slot_variation = random.randint(
            activity.schedule.SLOTS_PER_DAY // 20, activity.schedule.SLOTS_PER_DAY // 20
        )

        for day in candidate_days:
            free_slots_start = find_free_slots(
                day,
                block_length,
                table,
                start_from=clamp(
                    activity.min_start_slot + slot_variation,
                    0,
                    activity.schedule.SLOTS_PER_DAY - block_length,
                ),
            )
            if free_slots_start is not None:
                b = _Block(
                    activity_id=activity.id,
                    day=day,
                    start=free_slots_start,
                    length=block_length,
                )
                place_block(table, b)
                blocks[b.id] = b
                activity_to_blocks[activity.id].add(b.id)
                day_load[day] += 1
                used_days.add(day)
                placed = True
                break

        if not placed:
            for reduced_length in range(block_length - 1, 0, -1):
                for day in candidate_days:
                    free_slots_start = find_free_slots(
                        day,
                        reduced_length,
                        table,
                        start_from=activity.min_start_slot + slot_variation,
                    )
                    if free_slots_start is not None:
                        b = _Block(
                            activity_id=activity.id,
                            day=day,
                            start=free_slots_start,
                            length=reduced_length,
                        )
                        place_block(table, b)
                        blocks[b.id] = b
                        activity_to_blocks[activity.id].add(b.id)
                        day_load[day] += 1
                        used_days.add(day)
                        placed = True
                        break
                if placed:
                    break

        # if not placed:
        #     raise RuntimeError(
        #         f"Unable to place a block for activity {activity.id} with a length of {block_length}"
        #     )


def random_schedule(
    activity: _Activity,
    table: OverlapTable,
    blocks: dict[int, _Block],
    activity_to_blocks: ATB,
    day_load: list[int],
):
    needed_sessions = max(activity.frequency, 1)

    total_needed = max(activity.min_weekly_slots, needed_sessions)

    lengths = allocate_lengths(total_needed, needed_sessions, activity.max_block_slots)
    days = range(activity.schedule.SIZE)

    while len(lengths) != 0:
        block_length = lengths.pop()

        placed = False
        for day in days:
            free_slots_start = find_free_slots(
                day, block_length, table, start_from=random.randint(0, 23)
            )
            if free_slots_start is not None:
                b = _Block(
                    activity_id=activity.id,
                    day=day,
                    start=free_slots_start,
                    length=block_length,
                )
                place_block(table, b)
                blocks[b.id] = b
                activity_to_blocks[activity.id].add(b.id)
                day_load[day] += 1
                placed = True

        if not placed:
            for reduced_length in range(block_length - 1, 0, -1):
                for day in days:
                    free_slots_start = find_free_slots(
                        day, reduced_length, table, start_from=random.randint(0, 24)
                    )
                    if free_slots_start is not None:
                        b = _Block(
                            activity_id=activity.id,
                            day=day,
                            start=free_slots_start,
                            length=reduced_length,
                        )
                        place_block(table, b)
                        blocks[b.id] = b
                        activity_to_blocks[activity.id].add(b.id)
                        day_load[day] += 1
                        placed = True
                        break
                if placed:
                    break

        if not placed:
            raise RuntimeError(
                f"Unable to place a block for activity {activity.id} with a length of {block_length}"
            )


def place_fixed_blocks(
    table: OverlapTable,
    activities: list[_Activity],
    blocks: dict[int, _Block],
    activity_to_blocks: ATB,
    day_load: list[int],
):
    for activity in activities:
        for day, start, length in activity.fixed_blocks:
            if length > activity.max_block_slots:
                raise ValueError(
                    f"fixed block for activity {activity.id} exceeds the max size"
                )

            b = _Block(
                activity_id=activity.id, day=day, start=start, length=length, fixed=True
            )
            if not can_place(activity.schedule, table, b):
                raise ValueError(
                    f"fixed block for activity {activity.id} overlaps another block"
                )

            place_block(table, b)
            blocks[b.id] = b
            activity_to_blocks[activity.id].add(b.id)
            day_load[day] += 1


def greedy_initial(
    schedule: _Schedule,
    activities: list[_Activity],
    table: OverlapTable|None = None,
    blocks: dict[int, _Block] | None = None,
    activity_to_blocks: ATB | None = None,
    day_load:list[int]|None = None

):
    if table is None:
        table = [
            [set() for _ in range(schedule.SLOTS_PER_DAY)] for _ in range(schedule.SIZE)
        ]
    if activity_to_blocks is None:
        activity_to_blocks = {a.id: set() for a in activities}
    if blocks is None:
        blocks = {}
    if day_load is None:
        day_load = [0] * schedule.SIZE

    print(activity_to_blocks)

    place_fixed_blocks(table, activities, blocks, activity_to_blocks, day_load)

    sorted_activities = sorted(
        activities,
        key=lambda a: (a.priority, -int(a.even_spacing), -a.min_weekly_minutes),
    )

    for a in sorted_activities:
        if len(a.fixed_blocks) >= a.frequency:
            continue
        greedy_schedule(a, table, blocks, activity_to_blocks, day_load)

    return blocks, table, activity_to_blocks, day_load
