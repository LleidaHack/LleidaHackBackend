"""Deterministic multistart scheduling for parallel challenges and optional MLH.

Compare several greedy orderings rather than placing every MLH turn last.
This is a bounded heuristic, not a proof of a globally optimal schedule.
"""

from collections import Counter, defaultdict


def plan_schedule(presentations, start, end, duration, travel):
    fixed = [
        p for p in presentations if p.pinned or p.state not in {"waiting", "postponed"}
    ]
    pending = [p for p in presentations if p not in fixed]
    fixed_times = {
        p.id: getattr(p, "started_at", None) or p.scheduled_at for p in fixed
    }
    if any(value is None for value in fixed_times.values()):
        raise ValueError("Fixed or active presentations need a start time")
    best = None
    best_score = None
    for strategy in ("primary", "mlh", "load", "earliest_load", "earliest_team"):
        room_slots, team_slots = defaultdict(list), defaultdict(list)
        times = dict(fixed_times)

        def book(p, when, room_slots=room_slots, team_slots=team_slots):
            finish = getattr(p, "completed_at", None) or when + duration
            room_slots[p.room].append((when, finish))
            team_slots[p.group_id].append((when - travel, finish + travel))

        for p in fixed:
            book(p, times[p.id])
        remaining = list(pending)
        while remaining:
            room_load = Counter(p.room for p in remaining)
            team_load = Counter(p.group_id for p in remaining)

            def earliest(p, room_slots=room_slots, team_slots=team_slots):
                candidate = start
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

            chosen = min(remaining, key=priority)
            candidate = earliest(chosen)
            if candidate + duration > end:
                break
            times[chosen.id] = candidate
            book(chosen, candidate)
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
