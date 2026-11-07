from datetime import UTC, datetime, timedelta
from itertools import combinations
from types import SimpleNamespace

from src.impl.Operations.scheduler import plan_schedule

START = datetime(2026, 11, 7, 15, tzinfo=UTC)
DURATION = timedelta(minutes=10)
TRAVEL = timedelta(minutes=5)


def turn(id, room, team, **kwargs):
    return SimpleNamespace(
        id=id,
        room=room,
        track=room,
        group_id=team,
        position=id,
        pinned=False,
        state="waiting",
        scheduled_at=None,
        **kwargs,
    )


def assert_valid(turns, plan):
    assert plan is not None
    for a, b in combinations(turns, 2):
        if a.room == b.room or a.group_id == b.group_id:
            gap = DURATION + (TRAVEL if a.group_id == b.group_id else timedelta())
            assert abs(plan[a.id] - plan[b.id]) >= gap


def test_unbalanced_twenty_and_five_with_optional_mlh():
    turns = [turn(i, "busy" if i < 20 else "small", i) for i in range(25)]
    turns += [turn(100 + i, "mlh", i) for i in range(25)]
    plan = plan_schedule(turns, START, START + timedelta(hours=6), DURATION, TRAVEL)
    assert_valid(turns, plan)
    # MLH's 25 turns are the capacity lower bound: 250 minutes.
    assert max(plan.values()) + DURATION <= START + timedelta(minutes=250)
    assert any(plan[100 + i] < plan[i] for i in range(25))


def test_preserves_pins_and_reports_impossible_windows():
    turns = [turn(1, "one", 1), turn(2, "one", 2), turn(3, "mlh", 1)]
    turns[0].pinned = True
    turns[0].scheduled_at = START + timedelta(minutes=20)
    plan = plan_schedule(turns, START, START + timedelta(hours=1), DURATION, TRAVEL)
    assert_valid(turns, plan)
    assert plan[1] == turns[0].scheduled_at
    assert (
        plan_schedule(
            [turn(i, "one", i) for i in range(3)],
            START,
            START + DURATION * 2,
            DURATION,
            TRAVEL,
        )
        is None
    )


def test_only_opted_in_teams_receive_mlh_and_plan_is_deterministic():
    turns = [turn(i, "one" if i < 20 else "two", i) for i in range(25)] + [
        turn(100 + i, "mlh", i) for i in (0, 2, 21)
    ]
    plan = plan_schedule(turns, START, START + timedelta(hours=4), DURATION, TRAVEL)
    assert_valid(turns, plan)
    assert len(plan) == 28
    assert plan == plan_schedule(
        turns, START, START + timedelta(hours=4), DURATION, TRAVEL
    )
