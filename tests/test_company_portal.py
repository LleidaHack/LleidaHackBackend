from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy.orm import Session

from src.impl.Company.model import Company
from src.impl.CompanyPortal.mail_worker import deliver_one
from src.impl.CompanyPortal.model import PortalInvitation
from src.impl.Operations.model import EventOperations, Presentation


def prepare(client, engine, create_user, create_event, create_group):
    admin = create_user(role="organizer")
    hacker = create_user()
    event = create_event([hacker])
    group = create_group(event, [hacker])
    with Session(engine) as session:
        company = Company(name="Company A")
        session.add(company)
        session.flush()
        company_id = company.id
        session.add(
            EventOperations(
                event_id=event, config={"rooms": [{"id": "room-a", "title": "Room A"}]}
            )
        )
        session.add(
            Presentation(
                event_id=event,
                group_id=group.id,
                room="room-a",
                track="room-a",
                state="presenting",
                started_at=datetime.now(UTC),
            )
        )
        session.commit()
    body = {
        "company_id": company_id,
        "email": "company@example.test",
        "rooms": ["room-a"],
        "operation_id": str(uuid4()),
    }
    response = client.post(
        f"/v1/company-portal/manage/{event}/invite", headers=admin.headers, json=body
    )
    assert response.status_code == 200, response.text
    with Session(engine) as session:
        invitation = session.get(PortalInvitation, response.json()["id"])
        token = invitation.delivery_url.split("#invite=")[1]
    return admin, hacker, event, group.id, body, response.json(), token


def activate(client, token):
    response = client.post(
        "/v1/company-portal/setup",
        json={"token": token, "password": "CompanyTest2026!"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_company_sessions_notes_isolation_and_revocation(
    client, engine, create_user, create_event, create_group
):
    admin, hacker, event, group, body, invitation, token = prepare(
        client, engine, create_user, create_event, create_group
    )
    assert (
        client.post(
            f"/v1/company-portal/manage/{event}/invite",
            headers=admin.headers,
            json=body,
        ).json()
        == invitation
    )
    assert (
        client.post(
            f"/v1/company-portal/manage/{event}/invite",
            headers=hacker.headers,
            json={**body, "operation_id": str(uuid4())},
        ).status_code
        == 403
    )
    first = activate(client, token)
    assert (
        client.post(
            "/v1/company-portal/setup",
            json={"token": token, "password": "CompanyTest2026!"},
        ).status_code
        == 400
    )
    second = client.post(
        "/v1/company-portal/login",
        json={"email": body["email"], "password": "CompanyTest2026!"},
    ).json()
    second = {"Authorization": "Bearer " + second["access_token"]}
    url = f"/v1/company-portal/events/{event}"
    for headers in (first, second):
        snapshot = client.get(url, headers=headers)
        assert snapshot.status_code == 200
        assert snapshot.json()["duration_seconds"] == 300
        assert snapshot.json()["projects"][0]["id"] == group
        assert "email" not in snapshot.json()["projects"][0]
        assert snapshot.json()["presentations"][0]["started_at"]
    note = {"version": 0, "text": "Good project", "score": 8, "favorite": True}
    saved = client.put(url + f"/notes/{group}", headers=first, json=note)
    assert saved.status_code == 200, saved.text
    stale = client.put(url + f"/notes/{group}", headers=second, json=note)
    assert (
        stale.status_code == 409
        and stale.json()["detail"]["current"]["text"] == "Good project"
    )
    other_event = create_event()
    assert (
        client.get(
            f"/v1/company-portal/events/{other_event}", headers=first
        ).status_code
        == 403
    )
    assert (
        client.put(url + "/notes/999999", headers=first, json=note).status_code == 404
    )
    assert (
        client.put(
            url + "/winner",
            headers=first,
            json={"version": snapshot.json()["version"], "group_id": group},
        ).status_code
        == 200
    )
    assert (
        client.put(
            url + "/winner",
            headers=second,
            json={"version": snapshot.json()["version"], "group_id": group},
        ).status_code
        == 409
    )
    assert (
        client.delete(
            f"/v1/company-portal/manage/{event}/{body['company_id']}",
            headers=admin.headers,
        ).status_code
        == 200
    )
    assert client.get(url, headers=first).status_code == 403


def test_new_invitation_expires_old_link_and_password_reset_revokes_sessions(
    client, engine, create_user, create_event, create_group
):
    admin, _, event, _, body, _, token = prepare(
        client, engine, create_user, create_event, create_group
    )
    first = activate(client, token)
    new_invite = client.post(
        f"/v1/company-portal/manage/{event}/invite",
        headers=admin.headers,
        json={**body, "operation_id": str(uuid4())},
    ).json()
    with Session(engine) as session:
        row = session.get(PortalInvitation, new_invite["id"])
        new_token = row.delivery_url.split("#invite=")[1]
    second = activate(client, new_token)
    assert client.get("/v1/company-portal/events", headers=first).status_code == 401
    assert client.get("/v1/company-portal/events", headers=second).status_code == 200
    assert client.post("/v1/company-portal/logout", headers=second).status_code == 200
    assert client.get("/v1/company-portal/events", headers=second).status_code == 401


def test_invitation_outbox_does_not_replay_uncertain_sends(
    client, engine, create_user, create_event, create_group
):
    _, _, _, _, _, invite, _ = prepare(
        client, engine, create_user, create_event, create_group
    )
    calls = []

    class Mail:
        def get_template_by_name(self, name):
            return SimpleNamespace(id=10)

        def create_mail(self, body):
            calls.append("create")
            return SimpleNamespace(id=20)

        def send_mail_by_id(self, mail_id):
            calls.append("send")
            raise TimeoutError()

    assert deliver_one(engine, Mail())
    assert deliver_one(engine, Mail())
    assert not deliver_one(engine, Mail())
    assert calls == ["create", "send"]
    with Session(engine) as session:
        row = session.get(PortalInvitation, invite["id"])
        assert row.delivery_state == "uncertain" and row.delivery_url is None


def test_company_json_login_rejects_invalid_email_types(client):
    for email in ([], {}, None, 42):
        response = client.post(
            "/v1/company-portal/login", json={"email": email, "password": "Example123"}
        )
        assert response.status_code == 422


def test_separate_company_cannot_see_another_room_or_notes(
    client, engine, create_user, create_event, create_group
):
    from src.impl.CompanyPortal.model import PortalAccount, PortalGrant
    from src.utils.security import get_password_hash

    _, _, event, group, _, _, token = prepare(
        client, engine, create_user, create_event, create_group
    )
    first = activate(client, token)
    base = f"/v1/company-portal/events/{event}"
    assert (
        client.put(
            base + f"/notes/{group}",
            headers=first,
            json={"version": 0, "text": "Private company note"},
        ).status_code
        == 200
    )
    with Session(engine) as session:
        company = Company(name="Company B")
        session.add(company)
        session.flush()
        account = PortalAccount(
            company_id=company.id,
            email="second@example.test",
            password_hash=get_password_hash("CompanyTest2026!"),
        )
        session.add(account)
        session.flush()
        session.add(
            PortalGrant(account_id=account.id, event_id=event, rooms=["room-b"])
        )
        session.commit()
        second_account_id = account.id
    login = client.post(
        "/v1/company-portal/login",
        json={"email": "second@example.test", "password": "CompanyTest2026!"},
    ).json()
    second = {"Authorization": "Bearer " + login["access_token"]}
    snapshot = client.get(base, headers=second).json()
    assert snapshot["projects"] == [] and snapshot["presentations"] == []
    assert (
        client.put(
            base + f"/notes/{group}", headers=second, json={"version": 0}
        ).status_code
        == 404
    )
    with Session(engine) as session:
        grant = session.query(PortalGrant).filter_by(account_id=second_account_id).one()
        grant.rooms = ["room-a"]
        session.commit()
    assert client.get(base, headers=second).json()["projects"][0]["note"]["text"] == ""


def test_invitation_delivery_success_is_not_replayed(
    client, engine, create_user, create_event, create_group
):
    _, _, _, _, _, invite, _ = prepare(
        client, engine, create_user, create_event, create_group
    )
    calls = []

    class Mail:
        def get_template_by_name(self, name):
            assert name == "company_portal_invitation"
            return SimpleNamespace(id=10)

        def create_mail(self, body):
            assert "#invite=" in body.fields
            calls.append("create")
            return SimpleNamespace(id=20)

        def send_mail_by_id(self, mail_id):
            assert mail_id == 20
            calls.append("send")
            return SimpleNamespace(status_code=200)

    assert deliver_one(engine, Mail())
    assert deliver_one(engine, Mail())
    assert not deliver_one(engine, Mail())
    assert calls == ["create", "send"]
    with Session(engine) as session:
        row = session.get(PortalInvitation, invite["id"])
        assert row.delivery_state == "sent" and row.delivery_url is None


def test_portal_migration_round_trip_preserves_existing_events(engine, create_event):
    from alembic.config import Config
    from sqlalchemy import text

    from alembic import command

    event = create_event()
    with engine.connect() as conn:
        before = conn.execute(
            text("SELECT row_to_json(e)::text FROM event e WHERE id=:id"), {"id": event}
        ).scalar_one()
    command.downgrade(Config("alembic.ini"), "20261107_group_cascade")
    command.upgrade(Config("alembic.ini"), "head")
    with engine.connect() as conn:
        after = conn.execute(
            text("SELECT row_to_json(e)::text FROM event e WHERE id=:id"), {"id": event}
        ).scalar_one()
    assert before == after
