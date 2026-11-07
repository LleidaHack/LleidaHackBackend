# ruff: noqa: F811
"""Regressions for issues found while reviewing the event-operations rollout."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.impl.Operations.scheduler import plan_schedule
from src.utils.access import authorize_route
from tests.test_event_operations import prepare
from tests.test_tickets_vouchers import accept  # noqa: F401


def token(role, user_id=7):
    return SimpleNamespace(
        user_type="lleida_hacker",
        is_admin=False,
        available=True,
        access_role=role,
        user_id=user_id,
    )


def test_admin_route_matching_uses_whole_segments():
    admin = token("admin")
    # /v1/userConfig is not an identity route.
    authorize_route(admin, "PUT", "/v1/userConfig/7")
    # Revoking a lost badge is routine, like withdrawing an alert.
    authorize_route(admin, "DELETE", "/v1/event/3/vouchers/V123/assign")
    for method, path in (
        ("PUT", "/v1/user/8"),
        ("POST", "/v1/hacker/group/1/add/2"),
        ("DELETE", "/v1/event/3"),
        ("POST", "/v1/user/force-verify/8"),
    ):
        with pytest.raises(HTTPException):
            authorize_route(admin, method, path)


def test_absent_turns_without_time_do_not_block_scheduling():
    start = datetime(2026, 11, 7, 15, tzinfo=UTC)
    turns = [
        SimpleNamespace(
            id=1, room="a", track="a", group_id=1, position=1, pinned=False,
            state="absent", scheduled_at=None,
        ),
        SimpleNamespace(
            id=2, room="a", track="a", group_id=2, position=2, pinned=False,
            state="waiting", scheduled_at=None,
        ),
    ]  # fmt: skip
    plan = plan_schedule(
        turns, start, start + timedelta(hours=1), timedelta(minutes=10), timedelta()
    )
    assert plan is not None and plan[2] == start


def test_admin_can_manage_zero_point_activities_only(
    client, create_user, create_event, accept, engine
):
    _superadmin, _h, event, _code, _ = prepare(
        client, create_user, create_event, accept, engine
    )
    admin = create_user(role="admin")
    url = f"/v1/operations/{event}"

    def save(activities):
        config = client.get(url + "/manage", headers=admin.headers).json()
        config["activities"] = activities
        return client.put(
            url + "/config",
            headers=admin.headers,
            json={"version": config["version"], "config": config, "reason": "Agenda"},
        )

    start = datetime.now(UTC) + timedelta(hours=1)
    talk = {
        "id": "talk",
        "title": "Talk",
        "start": start.isoformat(),
        "end": (start + timedelta(hours=1)).isoformat(),
        "points": 0,
    }
    assert save([talk]).status_code == 200
    assert save([]).status_code == 200
    assert save([{**talk, "points": 5}]).status_code == 403


def test_hacker_scan_attempt_is_rejected_without_event_lock(
    client, create_user, create_event, accept, engine
):
    _o, h, event, code, meal = prepare(
        client, create_user, create_event, accept, engine
    )
    response = client.post(
        f"/v1/operations/{event}/scan",
        headers=h.headers,
        json={
            "operation_id": "00000000-0000-4000-8000-000000000001",
            "kind": "meal",
            "code": code,
            "target": str(meal),
        },
    )
    assert response.status_code == 403
