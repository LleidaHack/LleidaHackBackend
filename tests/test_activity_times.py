# ruff: noqa: F811
from uuid import uuid4

from sqlalchemy.orm import Session

from src.impl.Operations.model import CoinMovement, OperationAudit, ScanRecord
from tests.test_tickets_vouchers import accept, user_code  # noqa: F401


def test_timed_attempts_ranking_and_single_participation_reward(
    client, create_user, create_event, accept, engine, monkeypatch
):
    from src.configuration.Settings import settings

    # Exercise many distinct scan outcomes without the unrelated burst quota.
    monkeypatch.setattr(settings.rate_limit, "enabled", False)
    admin, staff = create_user(role="organizer"), create_user(role="lleidahacker")
    users = [create_user(name=f"Rider {i}") for i in range(3)]
    event = create_event(users)
    base = f"/v1/operations/{event}"
    config = client.get(base + "/manage", headers=admin.headers).json()
    config["activities"] = [
        {
            "id": id,
            "title": id,
            "start": "2026-11-20T12:00:00Z",
            "end": "2026-11-20T14:00:00Z",
            "points": 5,
            "timed": timed,
        }
        for id, timed in [("bull", True), ("other", True), ("normal", False)]
    ]
    response = client.put(
        base + "/config",
        headers=admin.headers,
        json={
            "config": config,
            "version": config["version"],
            "reason": "Set up activity times",
        },
    )
    assert response.status_code == 200, response.text
    badges = []
    for user in users:
        accept(admin, event, user)
        badge = client.post(
            f"/v1/event/{event}/vouchers/generate",
            headers=admin.headers,
            json={"count": 1},
        ).json()["vouchers"][0]["code"]
        assert (
            client.put(
                f"/v1/event/{event}/vouchers/{badge}/assign/{user_code(engine, user)}",
                headers=staff.headers,
            ).status_code
            == 200
        )
        badges.append(badge)

    def scan(i=0, duration=12345, target="bull", actor=staff, op=None):
        body = {
            "kind": "activity",
            "code": badges[i],
            "target": target,
            "operation_id": op or str(uuid4()),
        }
        if duration is not None:
            body["duration_ms"] = duration
        return client.post(base + "/scan", headers=actor.headers, json=body)

    for duration in [None, 0, -1, 3600001, 12.5, True, "12345"]:
        assert scan(duration=duration).status_code == 422
    assert scan(actor=users[0]).status_code == 403
    assert scan(target="normal").status_code == 422
    assert scan(target="missing").status_code == 404
    op = str(uuid4())
    first = scan(op=op)
    assert first.status_code == 200, first.text
    assert first.json()["duration_ms"] == 12345
    assert first.json()["points"] == 5
    assert scan(op=op).json() == first.json()
    assert scan(op=op, duration=25000).status_code == 409
    assert scan(op=op, actor=admin).status_code == 409
    assert scan(duration=25000).json()["balance"] == 5
    assert scan(duration=10000).status_code == 200
    assert scan(i=1, duration=25000).status_code == 200
    assert scan(i=2, duration=9000).status_code == 200
    assert scan(i=2, duration=999999, target="other").status_code == 200
    assert scan(i=0, duration=None, target="normal").status_code == 200
    assert scan(i=0, duration=None, target="normal").status_code == 409
    ranking = client.get(base + "/activities/bull/ranking", headers=admin.headers)
    assert ranking.status_code == 200
    assert ranking.json()["participants"] == [
        {
            "rank": 1,
            "user_id": users[0].id,
            "name": "Rider 0",
            "best_duration_ms": 25000,
            "attempts": 3,
        },
        {
            "rank": 1,
            "user_id": users[1].id,
            "name": "Rider 1",
            "best_duration_ms": 25000,
            "attempts": 1,
        },
        {
            "rank": 3,
            "user_id": users[2].id,
            "name": "Rider 2",
            "best_duration_ms": 9000,
            "attempts": 1,
        },
    ]
    with Session(engine) as session:
        assert (
            session.query(ScanRecord)
            .filter_by(
                event_id=event, user_id=users[0].id, kind="activity", target="bull"
            )
            .count()
            == 1
        )
        assert (
            session.query(CoinMovement)
            .join(OperationAudit)
            .filter(
                CoinMovement.event_id == event,
                CoinMovement.user_id == users[0].id,
                OperationAudit.details["target"].as_string() == "bull",
            )
            .count()
            == 1
        )
    for actor in (staff, users[0]):
        assert (
            client.get(
                base + "/activities/bull/ranking", headers=actor.headers
            ).status_code
            == 403
        )
    assert client.get(base + "/activities/bull/ranking").status_code == 401
    other_event = create_event()
    assert (
        client.get(
            f"/v1/operations/{other_event}/activities/bull/ranking",
            headers=admin.headers,
        ).status_code
        == 404
    )
    public = client.get(base + "/public").json()
    assert "participants" not in public
    # An older management client omitting the new flag must preserve it.
    config = client.get(base + "/manage", headers=admin.headers).json()
    for a in config["activities"]:
        a.pop("timed", None)
    updated = client.put(
        base + "/config",
        headers=admin.headers,
        json={
            "config": config,
            "version": config["version"],
            "reason": "Older client saves configuration",
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["activities"][0]["timed"] is True
