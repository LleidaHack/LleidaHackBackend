from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session


@pytest.fixture
def accept(client, engine):
    """Accept a registered hacker and optionally mark assistance as confirmed."""
    from src.impl.Event.model import HackerRegistration

    def do(organizer, event_id, user, confirmed=True):
        response = client.put(
            f"/v1/event/{event_id}/accept/{user.id}", headers=organizer.headers
        )
        assert response.status_code == 200, response.text
        if confirmed:
            with Session(engine) as session:
                registration = session.get(HackerRegistration, (user.id, event_id))
                registration.confirmed_assistance = True
                session.commit()

    return do


@pytest.fixture
def sent_mails(monkeypatch):
    """Capture the mails the ticket job creates (mail client is mocked in conftest)."""
    from src.impl.Mail.client import MailClient

    mails = []

    def create_mail(self, mail):
        mails.append(mail)
        return SimpleNamespace(id=len(mails))

    monkeypatch.setattr(MailClient, "create_mail", create_mail)
    return mails


def user_code(engine, user):
    from src.impl.User.model import User

    with Session(engine) as session:
        return session.get(User, user.id).code


def test_vouchers_are_generated_per_event_with_unique_codes(
    client, create_user, create_event
):
    organizer, hacker = create_user(role="organizer"), create_user()
    event_id = create_event()
    path = f"/v1/event/{event_id}/vouchers"
    assert client.post(
        f"{path}/generate", headers=hacker.headers, json={"count": 3}
    ).status_code in (401, 403)
    response = client.post(
        f"{path}/generate", headers=organizer.headers, json={"count": 3}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["created"] == 3
    codes = {v["code"] for v in body["vouchers"]}
    assert len(codes) == 3 and all(
        code.startswith("V") and len(code) == 9 for code in codes
    )
    assert all(v["hacker_id"] is None for v in body["vouchers"])
    assert (
        client.post(
            f"{path}/generate", headers=organizer.headers, json={"count": 0}
        ).status_code
        == 422
    )
    listed = client.get(f"{path}/", headers=organizer.headers).json()
    assert {v["code"] for v in listed} == codes
    assert client.get(f"{path}/summary", headers=organizer.headers).json() == {
        "total": 3,
        "assigned": 0,
        "unassigned": 3,
    }
    csv = client.get(f"{path}/export.csv", headers=organizer.headers)
    assert csv.status_code == 200 and csv.headers["content-type"].startswith("text/csv")
    assert csv.text.splitlines()[0] == "code,hacker_id,hacker_name,assigned_at"
    assert len(csv.text.splitlines()) == 4
    qr = client.get(f"{path}/{min(codes)}/qr.png", headers=organizer.headers)
    assert qr.status_code == 200 and qr.headers["content-type"] == "image/png"
    assert qr.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_ticket_mail_goes_only_to_accepted_and_confirmed(
    client, create_user, create_event, accept, engine, sent_mails
):
    from src.impl.Event.model import HackerRegistration
    from src.impl.Event.service import EventService

    organizer = create_user(role="organizer")
    confirmed, unconfirmed, pending = create_user(), create_user(), create_user()
    event_id = create_event([confirmed, unconfirmed, pending], name="HackEPS Test")
    accept(organizer, event_id, confirmed, confirmed=True)
    accept(organizer, event_id, unconfirmed, confirmed=False)
    sent_mails.clear()  # drop the acceptance mails

    status = client.get(
        f"/v1/event/{event_id}/tickets/status", headers=organizer.headers
    ).json()
    assert status == {
        **status,
        "eligible": 2,
        "sent": 0,
        "pending": 2,
        "running": False,
    }

    assert client.post(
        f"/v1/event/{event_id}/tickets/send", headers=confirmed.headers
    ).status_code in (401, 403)
    # run the background job synchronously to assert on its effects
    EventService().send_ticket_mails_background(event_id, audience="hacker")
    assert [m.receiver_mail for m in sent_mails] == [confirmed.email]
    name, event_name, role, code, qr_url, ticket_url = sent_mails[0].fields.split(",")
    assert (name, event_name, code) == (
        "Test User",
        "HackEPS Test",
        user_code(engine, confirmed),
    )
    assert qr_url.endswith(f"/v1/event/{event_id}/ticket/{code}/qr.png")
    assert role == "Hacker"
    assert ticket_url.endswith(f"/entrada/{event_id}/{code}")
    with Session(engine) as session:
        assert (
            session.get(HackerRegistration, (confirmed.id, event_id)).ticket_sent_at
            is not None
        )
        assert (
            session.get(HackerRegistration, (unconfirmed.id, event_id)).ticket_sent_at
            is None
        )

    status = client.get(
        f"/v1/event/{event_id}/tickets/status", headers=organizer.headers
    ).json()
    assert (status["eligible"], status["sent"], status["pending"]) == (2, 1, 1)

    # idempotent: a second run sends nothing unless forced
    EventService().send_ticket_mails_background(event_id, audience="hacker")
    assert len(sent_mails) == 1
    EventService().send_ticket_mails_background(event_id, force=True, audience="hacker")
    assert len(sent_mails) == 2

    response = client.post(
        f"/v1/event/{event_id}/tickets/send", headers=organizer.headers
    )
    assert response.status_code == 200 and response.json()["scheduled"] is True


def test_ticket_send_fails_fast_when_mail_service_is_down(
    client, create_user, create_event, monkeypatch
):
    from src.error.MailClientException import MailClientException
    from src.impl.Mail.client import MailClient

    def down(self):
        raise MailClientException("MailClient is not available")

    monkeypatch.setattr(MailClient, "ensure_initialized", down)
    organizer = create_user(role="organizer")
    event_id = create_event()
    assert (
        client.post(
            f"/v1/event/{event_id}/tickets/send", headers=organizer.headers
        ).status_code
        == 503
    )


def test_ticket_qr_is_public_but_only_for_confirmed_hackers(
    client, create_user, create_event, accept, engine
):
    organizer, confirmed, unconfirmed = (
        create_user(role="organizer"),
        create_user(),
        create_user(),
    )
    event_id = create_event([confirmed, unconfirmed])
    accept(organizer, event_id, confirmed, confirmed=True)
    accept(organizer, event_id, unconfirmed, confirmed=False)
    ok = client.get(
        f"/v1/event/{event_id}/ticket/{user_code(engine, confirmed)}/qr.png"
    )
    assert ok.status_code == 200 and ok.headers["content-type"] == "image/png"
    assert (
        client.get(
            f"/v1/event/{event_id}/ticket/{user_code(engine, unconfirmed)}/qr.png"
        ).status_code
        == 404
    )
    assert client.get(f"/v1/event/{event_id}/ticket/NOPE/qr.png").status_code == 404
    other_event = create_event([confirmed])
    assert (
        client.get(
            f"/v1/event/{other_event}/ticket/{user_code(engine, confirmed)}/qr.png"
        ).status_code
        == 404
    )


def test_hacker_sees_own_ticket_state(
    client, create_user, create_event, accept, engine
):
    organizer, hacker, outsider = (
        create_user(role="organizer"),
        create_user(),
        create_user(),
    )
    event_id = create_event([hacker])
    path = f"/v1/event/{event_id}/ticket/{hacker.id}"
    assert client.get(path, headers=outsider.headers).status_code in (401, 403)
    before = client.get(path, headers=hacker.headers).json()
    assert before["registered"] and not before["accepted"] and not before["has_ticket"]
    assert before["code"] is None and before["qr_url"] is None
    accept(organizer, event_id, hacker)
    after = client.get(path, headers=hacker.headers).json()
    assert after["has_ticket"] and after["code"] == user_code(engine, hacker)
    assert after["checked_in"] is False and after["voucher_code"] is None
    assert client.get(path, headers=organizer.headers).status_code == 200


def test_checkin_binds_voucher_and_voucher_works_for_meals(
    client, create_user, create_event, accept, engine
):
    organizer, hacker, other = (
        create_user(role="organizer"),
        create_user(),
        create_user(),
    )
    event_id = create_event([hacker, other])
    accept(organizer, event_id, hacker, confirmed=False)  # forced at the door
    accept(organizer, event_id, other)
    vouchers = client.post(
        f"/v1/event/{event_id}/vouchers/generate",
        headers=organizer.headers,
        json={"count": 2},
    ).json()["vouchers"]
    v1, v2 = vouchers[0]["code"], vouchers[1]["code"]
    code = user_code(engine, hacker)
    assign = f"/v1/event/{event_id}/vouchers/{v1}/assign/{code}"

    assert client.put(assign, headers=hacker.headers).status_code in (401, 403)
    # scanning a voucher where the ticket is expected is a clear error
    assert (
        client.put(
            f"/v1/event/{event_id}/vouchers/{v1}/assign/{v2}", headers=organizer.headers
        ).status_code
        == 400
    )
    response = client.put(assign, headers=organizer.headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["voucher_code"] == v1 and body["hacker_id"] == hacker.id
    assert body["message"] == "user haven't confirmed so we forced confirmation"
    assert (
        client.get(
            f"/v1/event/{event_id}/is_participant/{hacker.id}",
            headers=organizer.headers,
        ).json()
        is True
    )

    # the same voucher can't be given twice, nor a second voucher to the same hacker
    assert client.put(assign, headers=organizer.headers).status_code == 400
    assert (
        client.put(
            f"/v1/event/{event_id}/vouchers/{v1}/assign/{user_code(engine, other)}",
            headers=organizer.headers,
        ).status_code
        == 400
    )
    assert (
        client.put(
            f"/v1/event/{event_id}/vouchers/{v2}/assign/{code}",
            headers=organizer.headers,
        ).status_code
        == 400
    )
    assert (
        client.get(
            f"/v1/event/{event_id}/vouchers/summary", headers=organizer.headers
        ).json()["assigned"]
        == 1
    )

    ticket = client.get(
        f"/v1/event/{event_id}/ticket/{hacker.id}", headers=hacker.headers
    ).json()
    assert ticket["checked_in"] is True and ticket["voucher_code"] == v1

    # the voucher now identifies the hacker for scans during the event
    assert (
        client.get(f"/v1/user/code/{v1}", headers=organizer.headers).json()["id"]
        == hacker.id
    )
    assert (
        client.get(f"/v1/user/code/{v2}", headers=organizer.headers).status_code == 404
    )
    meal = client.post(
        "/v1/meal/",
        headers=organizer.headers,
        json={"name": "Dinner", "description": "", "event_id": event_id},
    ).json()["id"]
    assert (
        client.put(f"/v1/meal/{meal}/eat/{v1}", headers=organizer.headers).status_code
        == 200
    )
    assert (
        client.put(f"/v1/meal/{meal}/eat/{v1}", headers=organizer.headers).status_code
        == 400
    )  # already eaten
    assert (
        client.put(f"/v1/meal/{meal}/eat/{v2}", headers=organizer.headers).status_code
        == 404
    )  # unassigned voucher

    # a lost badge is released and a new one assigned; participation is kept
    freed = client.delete(
        f"/v1/event/{event_id}/vouchers/{v1}/assign", headers=organizer.headers
    )
    assert freed.status_code == 200 and freed.json()["hacker_id"] is None
    assert (
        client.put(
            f"/v1/event/{event_id}/vouchers/{v2}/assign/{code}",
            headers=organizer.headers,
        ).status_code
        == 200
    )
    assert (
        client.get(
            f"/v1/event/{event_id}/is_participant/{hacker.id}",
            headers=organizer.headers,
        ).json()
        is True
    )


def test_voucher_is_scoped_to_its_event_and_needs_accepted_hacker(
    client, create_user, create_event, accept, engine
):
    organizer, accepted, rejected = (
        create_user(role="organizer"),
        create_user(),
        create_user(),
    )
    event_id, other_event = create_event([accepted, rejected]), create_event()
    accept(organizer, event_id, accepted)
    voucher = client.post(
        f"/v1/event/{other_event}/vouchers/generate",
        headers=organizer.headers,
        json={"count": 1},
    ).json()["vouchers"][0]["code"]
    assert (
        client.put(
            f"/v1/event/{event_id}/vouchers/{voucher}/assign/{user_code(engine, accepted)}",
            headers=organizer.headers,
        ).status_code
        == 404
    )
    own = client.post(
        f"/v1/event/{event_id}/vouchers/generate",
        headers=organizer.headers,
        json={"count": 1},
    ).json()["vouchers"][0]["code"]
    assert (
        client.put(
            f"/v1/event/{event_id}/vouchers/{own}/assign/{user_code(engine, rejected)}",
            headers=organizer.headers,
        ).status_code
        == 400
    )
    assert (
        client.put(
            f"/v1/event/{event_id}/vouchers/{own}/assign/UNKNOWN",
            headers=organizer.headers,
        ).status_code
        == 404
    )


def test_wallet_download_uses_profile_code_and_eligibility(
    client, create_user, create_event, accept, engine, monkeypatch
):
    import src.impl.Event.service as service_module
    from src.configuration.Settings import settings

    organizer = create_user(role="organizer")
    confirmed, pending = create_user(), create_user()
    event_id = create_event([confirmed, pending])
    accept(organizer, event_id, confirmed)
    code = user_code(engine, confirmed)
    path = f"/v1/event/{event_id}/ticket/{code}/apple.pkpass"
    monkeypatch.setattr(settings, "apple_wallet_p12_path", "")
    assert client.get(path).status_code == 503
    for name, value in {
        "apple_wallet_p12_path": "/private/pass.p12",
        "apple_wallet_password_file": "/private/password",
        "apple_wallet_wwdr_path": "/private/wwdr.pem",
        "apple_wallet_team_id": "5F659SC689",
        "apple_wallet_pass_type_id": "pass.cat.lleidahack.tickets",
    }.items():
        monkeypatch.setattr(settings, name, value)
    seen = []

    def sign(config, event, hacker):
        seen.append(hacker.code)
        return b"signed-pass"

    monkeypatch.setattr(service_module, "build_pass", sign)
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.apple.pkpass"
    assert response.headers["cache-control"] == "private, no-store"
    assert seen == [code]
    legacy = client.get(path.replace("/apple.pkpass", "/view/apple.pkpass"))
    assert legacy.status_code == 200 and legacy.content == b"signed-pass"
    state = client.get(
        f"/v1/event/{event_id}/ticket/{confirmed.id}", headers=confirmed.headers
    ).json()
    assert state["code"] == code
    assert state["apple_wallet_url"].endswith(path)
    pending_code = user_code(engine, pending)
    assert (
        client.get(
            f"/v1/event/{event_id}/ticket/{pending_code}/apple.pkpass"
        ).status_code
        == 404
    )
    assert (
        client.get(f"/v1/event/{event_id}/ticket/unknown/apple.pkpass").status_code
        == 404
    )
    assert seen == [code]


def test_invitation_groups_include_staff_and_active_mentors_without_login(
    client, create_user, create_event, accept, engine, sent_mails, monkeypatch
):
    import src.impl.Event.service as service_module
    from src.configuration.Settings import settings
    from src.impl.Event.service import EventService
    from src.impl.User.model import User

    admin = create_user(role="admin")
    staff = create_user(role="lleidahacker")
    confirmed, unconfirmed = create_user(), create_user()
    event = create_event([confirmed, unconfirmed])
    accept(admin, event, confirmed)
    accept(admin, event, unconfirmed, confirmed=False)
    base = f"/v1/operations/{event}/mentors"
    created = client.post(
        base,
        headers=admin.headers,
        json={"name": "Mentor <Test>", "email": "MENTOR@example.test"},
    )
    assert created.status_code == 200, created.text
    mentor = created.json()["id"]
    missing = client.post(
        base, headers=admin.headers, json={"name": "No email"}
    ).json()["id"]
    assert (
        client.post(
            base, headers=admin.headers, json={"name": "Invalid", "email": "bad"}
        ).status_code
        == 422
    )
    status_path = f"/v1/event/{event}/tickets/status"
    status = client.get(status_path, headers=admin.headers).json()
    assert status["groups"]["Staff"]["eligible"] == 2
    assert status["groups"]["Mentor"] == {"eligible": 1, "sent": 0, "missing_email": 1}
    assert status["groups"]["Hacker"]["eligible"] == 1
    assert client.get(status_path, headers=staff.headers).status_code == 403
    scanner = client.get(
        f"/v1/operations/{event}/scanner", headers=staff.headers
    ).json()
    assert all("email" not in row for row in scanner["mentors"])
    sent_mails.clear()
    EventService().send_ticket_mails_background(event, audience="mentor")
    assert [m.receiver_mail for m in sent_mails] == ["mentor@example.test"]
    assert sent_mails[0].fields.split(",")[0] == "Mentor &lt;Test&gt;"
    assert sent_mails[0].fields.split(",")[2] == "Mentor"
    view_url = sent_mails[0].fields.split(",")[-1]
    code = sent_mails[0].fields.split(",")[3]
    assert view_url.endswith(f"/entrada/{event}/{code}")
    redirect = client.get(
        f"/v1/event/{event}/ticket/{code}/view", follow_redirects=False
    )
    assert redirect.status_code == 307
    assert redirect.headers["location"] == view_url
    assert redirect.headers["cache-control"] == "private, no-store"
    page = client.get(f"/v1/event/{event}/ticket/{code}/page")
    assert f"<code>{code}</code>" not in page.text
    assert "backend.main.lleidahack.dev" not in page.text
    assert f"{view_url}/qr.png" in page.text
    assert "ticket/hackeps-logo.png" in page.text
    assert page.status_code == 200 and "Mentor &lt;Test&gt;" in page.text
    assert page.headers["cache-control"] == "private, no-store"
    EventService().send_ticket_mails_background(event, audience="mentor")
    assert len(sent_mails) == 1
    # Editing invitation contact never changes login identity, and queues a new delivery.
    assert (
        client.patch(
            base + f"/{mentor}",
            headers=admin.headers,
            json={"email": "new@example.test"},
        ).status_code
        == 200
    )
    with Session(engine) as session:
        assert session.get(User, mentor).email == "mentor@example.test"
        mentor_code = session.get(User, mentor).code
    EventService().send_ticket_mails_background(event, audience="mentor")
    assert sent_mails[-1].receiver_mail == "new@example.test"
    # The same code can bind a physical badge, without a hacker registration.
    badges = client.post(
        f"/v1/event/{event}/vouchers/generate", headers=admin.headers, json={"count": 2}
    ).json()["vouchers"]
    for user_id, code, badge in (
        (mentor, mentor_code, badges[0]),
        (staff.id, user_code(engine, staff), badges[1]),
    ):
        assigned = client.put(
            f"/v1/event/{event}/vouchers/{badge['code']}/assign/{code}",
            headers=admin.headers,
        )
        assert assigned.status_code == 200, assigned.text
        assert assigned.json()["hacker_id"] == user_id
    # Wallet endpoint accepts both groups and still checks current eligibility.
    for field in (
        "apple_wallet_p12_path",
        "apple_wallet_password_file",
        "apple_wallet_wwdr_path",
        "apple_wallet_team_id",
        "apple_wallet_pass_type_id",
    ):
        monkeypatch.setattr(settings, field, "configured")
    seen = []
    monkeypatch.setattr(
        service_module,
        "build_pass",
        lambda config, event, user: seen.append(user.access_role) or b"pass",
    )
    assert (
        client.get(f"/v1/event/{event}/ticket/{mentor_code}/apple.pkpass").status_code
        == 200
    )
    assert (
        client.get(
            f"/v1/event/{event}/ticket/{user_code(engine, staff)}/apple.pkpass"
        ).status_code
        == 200
    )
    assert seen == ["mentor", "lleidahacker"]
    assert (
        client.patch(
            base + f"/{mentor}", headers=admin.headers, json={"active": False}
        ).status_code
        == 200
    )
    assert client.get(view_url).status_code == 404
    other = create_event()
    assert (
        client.get(f"/v1/event/{other}/ticket/{mentor_code}/qr.png").status_code == 404
    )
    assert (
        client.patch(
            base + f"/{missing}",
            headers=admin.headers,
            json={"email": "last@example.test"},
        ).status_code
        == 200
    )
    with Session(engine) as session:
        session.get(User, staff.id).is_deleted = True
        session.commit()
    assert (
        client.get(
            f"/v1/event/{event}/ticket/{user_code(engine, staff)}/qr.png"
        ).status_code
        == 404
    )


def test_staff_invitation_audience_tracks_delivery_and_rechecks_roles(
    client, create_user, create_event, sent_mails, engine
):
    from src.impl.Event.service import EventService
    from src.impl.User.model import User

    admin = create_user(role="admin")
    staff = create_user(role="lleidahacker")
    superadmin = create_user(role="superadmin")
    create_user()  # Not accepted/confirmed; must not receive an invitation.
    event = create_event()
    sent_mails.clear()
    EventService().send_ticket_mails_background(event, audience="staff")
    assert {m.receiver_mail for m in sent_mails} == {
        admin.email,
        staff.email,
        superadmin.email,
    }
    assert all(m.fields.split(",")[2] == "Staff" for m in sent_mails)
    EventService().send_ticket_mails_background(event, audience="staff")
    assert len(sent_mails) == 3
    status = client.get(
        f"/v1/event/{event}/tickets/status", headers=admin.headers
    ).json()
    assert status["groups"]["Staff"] == {"eligible": 3, "sent": 3, "missing_email": 0}
    assert (
        client.post(
            f"/v1/event/{event}/tickets/send?audience=unknown", headers=admin.headers
        ).status_code
        == 422
    )
    with Session(engine) as session:
        user = session.get(User, staff.id)
        code = user.code
        user.access_role = "hacker"
        session.commit()
    assert client.get(f"/v1/event/{event}/ticket/{code}/view").status_code == 404


def test_google_wallet_eligibility_and_direct_redirect(
    client, engine, create_user, create_event, accept, monkeypatch
):
    from src.configuration.Settings import settings
    from src.impl.Event import service

    organizer, confirmed, pending = (
        create_user(role="organizer"),
        create_user(),
        create_user(),
    )
    event = create_event([confirmed, pending])
    accept(organizer, event, confirmed)
    code = user_code(engine, confirmed)
    path = f"/v1/event/{event}/ticket/{code}/google-wallet"
    assert client.get(path).status_code == 503
    monkeypatch.setattr(settings, "google_wallet_enabled", True)
    monkeypatch.setattr(settings, "google_wallet_issuer_id", "12345")
    monkeypatch.setattr(settings, "google_wallet_credentials_path", "test.json")
    seen = []

    def save(config, event, user):
        seen.append(user.code)
        return "https://pay.google.com/gp/v/save/test-signed-token"

    monkeypatch.setattr(service, "build_save_url", save)
    result = client.get(path, follow_redirects=False)
    assert result.status_code == 303
    assert (
        result.headers["location"]
        == "https://pay.google.com/gp/v/save/test-signed-token"
    )
    assert result.headers["cache-control"] == "private, no-store"
    assert (
        client.get(
            f"/v1/event/{event}/ticket/{user_code(engine, pending)}/google-wallet"
        ).status_code
        == 404
    )
    assert seen == [code]


@pytest.mark.parametrize("target_role", ["hacker", "staff"])
def test_send_one_ticket_never_sends_to_the_other_recipients(
    client, create_user, create_event, accept, sent_mails, target_role
):
    organizer = create_user(role="organizer")
    first, second, pending = create_user(), create_user(), create_user()
    event = create_event([first, second, pending])
    accept(organizer, event, first)
    accept(organizer, event, second)
    selected = first if target_role == "hacker" else organizer
    sent_mails.clear()
    path = f"/v1/event/{event}/tickets/send?user_id={selected.id}"
    assert client.post(path, headers=first.headers).status_code in (401, 403)
    assert client.post(path, headers=organizer.headers).status_code == 200
    assert [mail.receiver_mail for mail in sent_mails] == [selected.email]
    assert client.post(path, headers=organizer.headers).status_code == 409
    assert (
        client.post(path + "&force=true", headers=organizer.headers).status_code == 200
    )
    assert [mail.receiver_mail for mail in sent_mails] == [selected.email] * 2
    assert (
        client.post(
            f"/v1/event/{event}/tickets/send?user_id={pending.id}&force=true",
            headers=organizer.headers,
        ).status_code
        == 400
    )
    assert (
        client.post(
            f"/v1/event/{event}/tickets/send?user_id=999999&force=true",
            headers=organizer.headers,
        ).status_code
        == 400
    )
    assert len(sent_mails) == 2
