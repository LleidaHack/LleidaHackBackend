# ruff: noqa: F811
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from src.impl.Company.model import Company
from src.impl.CompanyPortal.model import PortalAccount, PortalGrant
from src.impl.HackerGroup.model import HackerGroup
from src.impl.Operations.model import EventOperations, OperationAudit, Presentation
from src.utils.security import get_password_hash
from tests.test_tickets_vouchers import accept, user_code  # noqa: F401


def test_one_member_starts_team_calls_next_and_mlh_does_not_overlap(
    client, create_user, create_event, create_group, accept, engine
):
    admin, staff = create_user(role="organizer"), create_user(role="lleidahacker")
    members = [create_user() for _ in range(4)]
    event = create_event(members)
    groups = [
        create_group(event, members[:2]),
        create_group(event, [members[2]]),
        create_group(event, [members[3]]),
    ]
    badges = []
    for member in members:
        accept(admin, event, member)
        badge = client.post(
            f"/v1/event/{event}/vouchers/generate",
            headers=admin.headers,
            json={"count": 1},
        ).json()["vouchers"][0]["code"]
        assert (
            client.put(
                f"/v1/event/{event}/vouchers/{badge}/assign/{user_code(engine, member)}",
                headers=staff.headers,
            ).status_code
            == 200
        )
        badges.append(badge)
    base = f"/v1/operations/{event}"
    config = client.get(base + "/manage", headers=admin.headers).json()
    config.update(
        phase="judging",
        challenges_released=True,
        rooms=[{"id": "one", "title": "Room One"}, {"id": "mlh", "title": "MLH"}],
    )
    assert (
        client.put(
            base + "/config",
            headers=admin.headers,
            json={
                "version": config["version"],
                "config": config,
                "reason": "Prepare judging test",
            },
        ).status_code
        == 200
    )
    with Session(engine) as session:
        names = [session.get(HackerGroup, g.id).name for g in groups]
        for i, group in enumerate(groups):
            session.add(
                Presentation(
                    event_id=event,
                    group_id=group.id,
                    room="one",
                    track="one",
                    position=i,
                )
            )
            session.add(
                Presentation(
                    event_id=event,
                    group_id=group.id,
                    room="mlh",
                    track="mlh",
                    position=i,
                )
            )
        session.commit()

    def scan(code, room="one", actor=staff, operation_id=None):
        return client.post(
            base + "/scan",
            headers=actor.headers,
            json={
                "operation_id": operation_id or str(uuid4()),
                "kind": "judging_start",
                "code": code,
                "target": room,
            },
        )

    assert scan(badges[0], actor=members[0]).status_code == 403
    assert scan(user_code(engine, members[0])).status_code == 422
    op = str(uuid4())
    first = scan(badges[0], operation_id=op)
    assert first.status_code == 200, first.text
    assert first.json()["next_team"] == names[1]
    assert scan(badges[0], operation_id=op).json() == first.json()
    # A different teammate's badge is harmless and does not advance the room.
    assert scan(badges[1]).json()["already_presenting"]
    assert scan(badges[0], "mlh").status_code == 409
    # A new badge cannot silently finish the previous presentation.
    assert scan(badges[2]).status_code == 409
    with Session(engine) as session:
        turn = (
            session.query(Presentation)
            .filter_by(event_id=event, group_id=groups[0].id, room="one")
            .one()
        )
        assert turn.started_at is None and turn.state == "presenting"
        turn_id, version = turn.id, turn.version
        company = Company(name="Judges")
        session.add(company)
        session.flush()
        account = PortalAccount(
            company_id=company.id,
            email="judges@example.test",
            password_hash=get_password_hash("CompanyTest2026!"),
        )
        session.add(account)
        session.flush()
        session.add(PortalGrant(account_id=account.id, event_id=event, rooms=["one"]))
        session.commit()
    login = client.post(
        "/v1/company-portal/login",
        json={"email": "judges@example.test", "password": "CompanyTest2026!"},
    ).json()
    headers = {"Authorization": "Bearer " + login["access_token"]}
    url = f"/v1/company-portal/events/{event}/presentations/{turn_id}/action"
    started = client.post(
        url,
        headers=headers,
        json={"action": "start", "version": version, "operation_id": str(uuid4())},
    )
    assert started.status_code == 200, started.text
    finished = client.post(
        url,
        headers=headers,
        json={
            "action": "finish",
            "version": started.json()["version"],
            "operation_id": str(uuid4()),
        },
    )
    assert finished.status_code == 200, finished.text
    second = scan(badges[2])
    assert second.status_code == 200 and second.json()["next_team"] is None
    assert scan(badges[0]).status_code == 409
    # Completed teams need travel time before MLH; waiting/called teams are not called twice.
    assert scan(badges[0], "mlh").status_code == 409
    with Session(engine) as session:
        turn = (
            session.query(Presentation)
            .filter_by(event_id=event, group_id=groups[0].id, room="one")
            .one()
        )
        assert turn.state == "done" and turn.started_at and turn.completed_at
        turn.completed_at = datetime.now(UTC) - timedelta(minutes=6)
        session.commit()
    mlh = scan(badges[0], "mlh")
    assert mlh.status_code == 200, mlh.text
    assert mlh.json()["next_team"] == names[2]
    public = client.get(base + "/public").json()
    room_turns = [p for p in public["presentations"] if p["room"] == "one"]
    assert room_turns[0]["state"] == "presenting"
    active = [
        p for p in public["presentations"] if p["state"] in {"called", "presenting"}
    ]
    assert len({p["group_id"] for p in active}) == len(active)
    with Session(engine) as session:
        row = session.get(EventOperations, event)
        row.config = {
            **row.config,
            "rooms": [
                {"id": "one", "title": "Room One", "paused": True},
                {"id": "mlh", "title": "MLH"},
            ],
        }
        session.commit()
    assert scan(badges[3]).status_code == 409
    with Session(engine) as session:
        audits = session.query(OperationAudit).filter_by(event_id=event).all()
        assert any(
            a.action == "judging_start" and a.details.get("transitions") for a in audits
        )
