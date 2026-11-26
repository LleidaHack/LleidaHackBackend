"""Deterministic multistart scheduling for parallel challenges and optional MLH.

Compare several greedy orderings rather than placing every MLH turn last.
This is a bounded heuristic, not a proof of a globally optimal schedule.
"""

from collections import Counter, defaultdict


def plan_schedule(presentations, start, end, duration, travel, ribo_teams=frozenset()):
    # Absent teams neither occupy a room nor need a start time.
    presentations = [p for p in presentations if p.state != "absent"]
    fixed = [
        p for p in presentations if p.pinned or p.state not in {"waiting", "postponed"}
    ]
    pending = [p for p in presentations if p not in fixed]

    def fixed_time(p):
        when = getattr(p, "started_at", None) or p.scheduled_at
        if when is not None:
            return when
        # Teams called or scanned in before their timer starts, or pinned
        # without a time, have no start yet: they hold the room from the
        # planning start. Finished turns end at their recorded completion.
        completed = getattr(p, "completed_at", None)
        return completed - duration if completed is not None else start

    fixed_times = {p.id: fixed_time(p) for p in fixed}

    def is_priority(p):
        return p.track != "mlh" and p.group_id in ribo_teams

    best = None
    best_score = None
    for strategy in ("primary", "mlh", "load", "earliest_load", "earliest_team"):
        room_slots, team_slots = defaultdict(list), defaultdict(list)
        times = dict(fixed_times)

        def book(p, when, room_slots=room_slots, team_slots=team_slots):
            finish = getattr(p, "completed_at", None) or when + duration
            room_slots[p.room].append((when, finish))
            team_slots[p.group_id].append((when - travel, finish + travel))

        priority_end = {}
        for p in fixed:
            book(p, times[p.id])
            if is_priority(p):
                priority_end[p.room] = max(
                    priority_end.get(p.room, start), times[p.id] + duration
                )
        remaining = list(pending)
        while remaining:
            room_load = Counter(p.room for p in remaining)
            team_load = Counter(p.group_id for p in remaining)

            def earliest(
                p,
                room_slots=room_slots,
                team_slots=team_slots,
                priority_end=priority_end,
            ):
                candidate = (
                    priority_end.get(p.room, start)
                    if p.track != "mlh" and not is_priority(p)
                    else start
                )
                for left, right in sorted(room_slots[p.room] + team_slots[p.group_id]):
                    if candidate + duration <= left:
                        break
                    candidate = max(candidate, right)
                return candidate

            def priority(
                p,
                strategy=strategy,
                room_load=room_load,
                team_load=team_load,
                earliest=earliest,
            ):
                tie = (p.position, p.id)
                if strategy == "primary":
                    return (p.track == "mlh", *tie)
                if strategy == "mlh":
                    return (p.track != "mlh", *tie)
                if strategy == "load":
                    return (-room_load[p.room], -team_load[p.group_id], *tie)
                if strategy == "earliest_load":
                    return (
                        earliest(p),
                        -room_load[p.room],
                        -team_load[p.group_id],
                        *tie,
                    )
                return (earliest(p), -team_load[p.group_id], -room_load[p.room], *tie)

            priority_rooms = {p.room for p in remaining if is_priority(p)}
            eligible = (
                p
                for p in remaining
                if p.room not in priority_rooms or is_priority(p) or p.track == "mlh"
            )
            chosen = min(eligible, key=priority)
            candidate = earliest(chosen)
            if candidate + duration > end:
                break
            times[chosen.id] = candidate
            book(chosen, candidate)
            if is_priority(chosen):
                priority_end[chosen.room] = max(
                    priority_end.get(chosen.room, start), candidate + duration
                )
            remaining.remove(chosen)
        if remaining:
            continue
        score = (
            max((t + duration for t in times.values()), default=start),
            sum((t - start).total_seconds() for t in times.values()),
        )
        if best_score is None or score < best_score:
            best, best_score = times, score
    return best
