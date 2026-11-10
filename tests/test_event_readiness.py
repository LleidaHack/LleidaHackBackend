# ruff: noqa: F811
"""Local event rehearsal, recovery permissions and final decision concurrency."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from src.impl.Company.model import Company
from src.impl.CompanyPortal.model import PortalAccount, PortalGrant
from src.impl.Event.model import HackerRegistration
from src.impl.Operations.model import EventOperations, OperationAudit, Presentation
from src.utils.security import get_password_hash
from tests.test_event_operations import prepare
from tests.test_tickets_vouchers import accept  # noqa: F401


def test_event_rehearsal(
    client, engine, create_user, create_event, create_group, accept
):
    admin, hacker, event, badge, meal = prepare(
        client, create_user, create_event, accept, engine
    )
    group = create_group(event, [hacker])
    base = f"/v1/operations/{event}"
    with Session(engine) as session:
        config = session.get(EventOperations, event)
        config.config = {
            **config.config,
            "phase": "judging",
            "challenges_released": True,
            "rooms": [{"id": "room-a", "title": "Room A", "paused": False}],
        }
        registration = session.get(HackerRegistration, (hacker.id, event))
        registration.food_restrictions = "Gluten"
        company = Company(name="Rehearsal company")
        session.add(company)
        session.flush()
        account = PortalAccount(
            company_id=company.id,
            email="rehearsal@example.test",
            password_hash=get_password_hash("CompanyTest2026!"),
        )
        session.add(account)
        session.flush()
        session.add(
            PortalGrant(account_id=account.id, event_id=event, rooms=["room-a"])
        )
        turn = Presentation(
            event_id=event,
            group_id=group.id,
            room="room-a",
            track="room-a",
            state="waiting",
        )
        session.add(turn)
        session.flush()
        turn_id, company_id = turn.id, company.id
        session.commit()
    assert client.get(base + "/status", headers=hacker.headers).status_code == 403
    meal_body = {
        "operation_id": str(uuid4()),
        "kind": "meal",
        "code": badge,
        "target": str(meal),
    }
    assert (
        client.post(base + "/scan", headers=admin.headers, json=meal_body).status_code
        == 200
    )
    state = client.get(base + "/status", headers=admin.headers).json()
    assert state["attendance"] == {"expected": 1, "checked_in": 1, "pending": 0}
    assert state["dietary"] == [{"restriction": "Gluten", "count": 1}]
    assert state["meals"][0]["served"] == 1
    incident = {
        "title": "Projector unavailable",
        "details": "Replace HDMI cable",
        "operation_id": str(uuid4()),
    }
    created = client.post(base + "/incidents", headers=admin.headers, json=incident)
    assert created.status_code == 200, created.text
    assert (
        client.post(base + "/incidents", headers=admin.headers, json=incident).json()
        == created.json()
    )
    incident_url = base + f"/incidents/{created.json()['id']}"
    assert (
        client.patch(
            incident_url,
            headers=admin.headers,
            json={"version": 0, "status": "resolved"},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            incident_url, headers=admin.headers, json={"version": 0, "status": "open"}
        ).status_code
        == 409
    )
    scan = client.post(
        base + "/scan",
        headers=admin.headers,
        json={
            "operation_id": str(uuid4()),
            "kind": "judging_start",
            "code": badge,
            "target": "room-a",
        },
    )
    assert scan.status_code == 200, scan.text
    assert scan.json()["timer_started"] is False
    login = client.post(
        "/v1/company-portal/login",
        json={"email": "rehearsal@example.test", "password": "CompanyTest2026!"},
    )
    company_headers = {"Authorization": "Bearer " + login.json()["access_token"]}
    portal = f"/v1/company-portal/events/{event}"
    snapshot = client.get(portal, headers=company_headers).json()
    version = snapshot["presentations"][0]["version"]
    for action in ["start", "extend", "finish"]:
        response = client.post(
            portal + f"/presentations/{turn_id}/action",
            headers=company_headers,
            json={"action": action, "version": version, "operation_id": str(uuid4())},
        )
        assert response.status_code == 200, response.text
        version = response.json()["version"]
    note = client.put(
        portal + f"/notes/{group.id}",
        headers=company_headers,
        json={"version": 0, "text": "Clear demo", "score": 9},
    )
    assert note.status_code == 200
    snapshot = client.get(portal, headers=company_headers).json()
    chosen = client.put(
        portal + "/winner",
        headers=company_headers,
        json={"version": snapshot["version"], "group_id": group.id},
    )
    assert chosen.status_code == 200, chosen.text
    decision = {
        "version": chosen.json()["version"],
        "group_id": group.id,
        "operation_id": str(uuid4()),
    }
    final = client.post(portal + "/finalize", headers=company_headers, json=decision)
    assert final.status_code == 200, final.text
    assert (
        client.post(portal + "/finalize", headers=company_headers, json=decision).json()
        == final.json()
    )
    assert (
        client.put(
            portal + f"/notes/{group.id}",
            headers=company_headers,
            json={"version": 1, "text": "Late edit"},
        ).status_code
        == 409
    )
    assert (
        client.put(
            portal + "/winner",
            headers=company_headers,
            json={"version": final.json()["version"], "group_id": None},
        ).status_code
        == 409
    )
    reopen = f"/v1/company-portal/manage/{event}/{company_id}/reopen"
    assert (
        client.post(
            reopen,
            headers=hacker.headers,
            json={"version": final.json()["version"], "reason": "Correct decision"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            reopen,
            headers=admin.headers,
            json={"version": final.json()["version"], "reason": "Correct decision"},
        ).status_code
        == 200
    )
    assert client.get(portal, headers=company_headers).json()["finalized_at"] is None
    with Session(engine) as session:
        assert (
            session.query(OperationAudit)
            .filter_by(event_id=event, action="company.finalize")
            .count()
            == 1
        )
        assert (
            session.query(OperationAudit)
            .filter_by(event_id=event, action="company.reopen")
            .count()
            == 1
        )


def test_judging_recovery_is_versioned_and_preserves_active_teams(
    client, engine, create_user, create_event, create_group
):
    admin, hacker = create_user(role="organizer"), create_user()
    event = create_event([hacker])
    group = create_group(event, [hacker])
    with Session(engine) as session:
        session.add(
            EventOperations(
                event_id=event,
                config={
                    "phase": "judging",
                    "challenges_released": True,
                    "rooms": [
                        {"id": "a", "title": "A", "paused": False},
                        {"id": "b", "title": "B", "paused": False},
                    ],
                },
            )
        )
        turn = Presentation(
            event_id=event, group_id=group.id, room="a", track="a", state="called"
        )
        session.add(turn)
        session.flush()
        turn_id = turn.id
        session.commit()
    base = f"/v1/operations/{event}"
    url = base + f"/presentations/{turn_id}/recovery"
    body = {
        "version": 0,
        "action": "absent",
        "reason": "Team did not arrive",
        "operation_id": str(uuid4()),
    }
    assert client.post(url, headers=hacker.headers, json=body).status_code == 403
    result = client.post(url, headers=admin.headers, json=body)
    assert result.status_code == 200, result.text
    assert client.post(url, headers=admin.headers, json=body).json() == result.json()
    assert (
        client.post(
            url, headers=admin.headers, json={**body, "operation_id": str(uuid4())}
        ).status_code
        == 409
    )
    state = client.get(base + "/status", headers=admin.headers).json()
    pause = {"version": state["version"], "paused": True, "reason": "Technical issue"}
    assert (
        client.post(
            base + "/rooms/a/pause", headers=admin.headers, json=pause
        ).status_code
        == 200
    )
    assert (
        client.post(
            base + "/rooms/a/pause", headers=admin.headers, json=pause
        ).status_code
        == 409
    )
    result = client.post(
        url,
        headers=admin.headers,
        json={
            "version": 1,
            "action": "requeue",
            "reason": "Team returned",
            "operation_id": str(uuid4()),
        },
    )
    assert result.status_code == 200, result.text
    with Session(engine) as session:
        turn = session.get(Presentation, turn_id)
        assert turn.state == "waiting" and turn.started_at is None
        turn.state = "presenting"
        turn.started_at = datetime.now(UTC)
        session.commit()
    assert (
        client.post(
            url,
            headers=admin.headers,
            json={
                "version": 2,
                "action": "move",
                "room": "b",
                "reason": "Wrong room",
                "operation_id": str(uuid4()),
            },
        ).status_code
        == 409
    )
