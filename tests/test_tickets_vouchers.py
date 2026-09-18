from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session


@pytest.fixture
def accept(client, engine):
    """Accept a registered hacker and optionally mark assistance as confirmed."""
    from src.impl.Event.model import HackerRegistration

    def do(organizer, event_id, user, confirmed=True):
        response = client.put(f"/v1/event/{event_id}/accept/{user.id}", headers=organizer.headers)
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


def test_vouchers_are_generated_per_event_with_unique_codes(client, create_user, create_event):
    organizer, hacker = create_user(role="organizer"), create_user()
    event_id = create_event()
    path = f"/v1/event/{event_id}/vouchers"
    assert client.post(f"{path}/generate", headers=hacker.headers, json={"count": 3}).status_code in (401, 403)
    response = client.post(f"{path}/generate", headers=organizer.headers, json={"count": 3})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["created"] == 3
    codes = {v["code"] for v in body["vouchers"]}
    assert len(codes) == 3 and all(code.startswith("V") and len(code) == 9 for code in codes)
    assert all(v["hacker_id"] is None for v in body["vouchers"])
    assert client.post(f"{path}/generate", headers=organizer.headers, json={"count": 0}).status_code == 422
    listed = client.get(f"{path}/", headers=organizer.headers).json()
    assert {v["code"] for v in listed} == codes
    assert client.get(f"{path}/summary", headers=organizer.headers).json() == {"total": 3, "assigned": 0, "unassigned": 3}
    csv = client.get(f"{path}/export.csv", headers=organizer.headers)
    assert csv.status_code == 200 and csv.headers["content-type"].startswith("text/csv")
    assert csv.text.splitlines()[0] == "code,hacker_id,hacker_name,assigned_at"
    assert len(csv.text.splitlines()) == 4
    qr = client.get(f"{path}/{min(codes)}/qr.png", headers=organizer.headers)
    assert qr.status_code == 200 and qr.headers["content-type"] == "image/png"
    assert qr.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_ticket_mail_goes_only_to_accepted_and_confirmed(client, create_user, create_event, accept, engine, sent_mails):
    from src.impl.Event.model import HackerRegistration
    from src.impl.Event.service import EventService

    organizer = create_user(role="organizer")
    confirmed, unconfirmed, pending = create_user(), create_user(), create_user()
    event_id = create_event([confirmed, unconfirmed, pending], name="HackEPS Test")
    accept(organizer, event_id, confirmed, confirmed=True)
    accept(organizer, event_id, unconfirmed, confirmed=False)
    sent_mails.clear()  # drop the acceptance mails

    status = client.get(f"/v1/event/{event_id}/tickets/status", headers=organizer.headers).json()
    assert status == {**status, "eligible": 1, "sent": 0, "pending": 1, "running": False}

    assert client.post(f"/v1/event/{event_id}/tickets/send", headers=confirmed.headers).status_code in (401, 403)
    # run the background job synchronously to assert on its effects
    EventService().send_ticket_mails_background(event_id)
    assert [m.receiver_mail for m in sent_mails] == [confirmed.email]
    name, event_name, code, qr_url = sent_mails[0].fields.split(",")
    assert (name, event_name, code) == ("Test User", "HackEPS Test", user_code(engine, confirmed))
    assert qr_url.endswith(f"/v1/event/{event_id}/ticket/{code}/qr.png")
    with Session(engine) as session:
        assert session.get(HackerRegistration, (confirmed.id, event_id)).ticket_sent_at is not None
        assert session.get(HackerRegistration, (unconfirmed.id, event_id)).ticket_sent_at is None

    status = client.get(f"/v1/event/{event_id}/tickets/status", headers=organizer.headers).json()
    assert (status["eligible"], status["sent"], status["pending"]) == (1, 1, 0)

    # idempotent: a second run sends nothing unless forced
    EventService().send_ticket_mails_background(event_id)
    assert len(sent_mails) == 1
    EventService().send_ticket_mails_background(event_id, force=True)
    assert len(sent_mails) == 2

    response = client.post(f"/v1/event/{event_id}/tickets/send", headers=organizer.headers)
    assert response.status_code == 200 and response.json()["scheduled"] is True


def test_ticket_send_fails_fast_when_mail_service_is_down(client, create_user, create_event, monkeypatch):
    from src.error.MailClientException import MailClientException
    from src.impl.Mail.client import MailClient

    def down(self):
        raise MailClientException("MailClient is not available")

    monkeypatch.setattr(MailClient, "ensure_initialized", down)
    organizer = create_user(role="organizer")
    event_id = create_event()
    assert client.post(f"/v1/event/{event_id}/tickets/send", headers=organizer.headers).status_code == 503


def test_ticket_qr_is_public_but_only_for_confirmed_hackers(client, create_user, create_event, accept, engine):
    organizer, confirmed, unconfirmed = create_user(role="organizer"), create_user(), create_user()
    event_id = create_event([confirmed, unconfirmed])
    accept(organizer, event_id, confirmed, confirmed=True)
    accept(organizer, event_id, unconfirmed, confirmed=False)
    ok = client.get(f"/v1/event/{event_id}/ticket/{user_code(engine, confirmed)}/qr.png")
    assert ok.status_code == 200 and ok.headers["content-type"] == "image/png"
    assert client.get(f"/v1/event/{event_id}/ticket/{user_code(engine, unconfirmed)}/qr.png").status_code == 404
    assert client.get(f"/v1/event/{event_id}/ticket/NOPE/qr.png").status_code == 404
    other_event = create_event([confirmed])
    assert client.get(f"/v1/event/{other_event}/ticket/{user_code(engine, confirmed)}/qr.png").status_code == 404


def test_hacker_sees_own_ticket_state(client, create_user, create_event, accept, engine):
    organizer, hacker, outsider = create_user(role="organizer"), create_user(), create_user()
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


def test_checkin_binds_voucher_and_voucher_works_for_meals(client, create_user, create_event, accept, engine):
    organizer, hacker, other = create_user(role="organizer"), create_user(), create_user()
    event_id = create_event([hacker, other])
    accept(organizer, event_id, hacker, confirmed=False)  # forced at the door
    accept(organizer, event_id, other)
    vouchers = client.post(f"/v1/event/{event_id}/vouchers/generate", headers=organizer.headers, json={"count": 2}).json()["vouchers"]
    v1, v2 = vouchers[0]["code"], vouchers[1]["code"]
    code = user_code(engine, hacker)
    assign = f"/v1/event/{event_id}/vouchers/{v1}/assign/{code}"

    assert client.put(assign, headers=hacker.headers).status_code in (401, 403)
    # scanning a voucher where the ticket is expected is a clear error
    assert client.put(f"/v1/event/{event_id}/vouchers/{v1}/assign/{v2}", headers=organizer.headers).status_code == 400
    response = client.put(assign, headers=organizer.headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["voucher_code"] == v1 and body["hacker_id"] == hacker.id
    assert body["message"] == "user haven't confirmed so we forced confirmation"
    assert client.get(f"/v1/event/{event_id}/is_participant/{hacker.id}", headers=organizer.headers).json() is True

    # the same voucher can't be given twice, nor a second voucher to the same hacker
    assert client.put(assign, headers=organizer.headers).status_code == 400
    assert client.put(f"/v1/event/{event_id}/vouchers/{v1}/assign/{user_code(engine, other)}", headers=organizer.headers).status_code == 400
    assert client.put(f"/v1/event/{event_id}/vouchers/{v2}/assign/{code}", headers=organizer.headers).status_code == 400
    assert client.get(f"/v1/event/{event_id}/vouchers/summary", headers=organizer.headers).json()["assigned"] == 1

    ticket = client.get(f"/v1/event/{event_id}/ticket/{hacker.id}", headers=hacker.headers).json()
    assert ticket["checked_in"] is True and ticket["voucher_code"] == v1

    # the voucher now identifies the hacker for scans during the event
    assert client.get(f"/v1/user/code/{v1}", headers=organizer.headers).json()["id"] == hacker.id
    assert client.get(f"/v1/user/code/{v2}", headers=organizer.headers).status_code == 404
    meal = client.post("/v1/meal/", headers=organizer.headers, json={"name": "Dinner", "description": "", "event_id": event_id}).json()["id"]
    assert client.put(f"/v1/meal/{meal}/eat/{v1}", headers=organizer.headers).status_code == 200
    assert client.put(f"/v1/meal/{meal}/eat/{v1}", headers=organizer.headers).status_code == 400  # already eaten
    assert client.put(f"/v1/meal/{meal}/eat/{v2}", headers=organizer.headers).status_code == 404  # unassigned voucher

    # a lost badge is released and a new one assigned; participation is kept
    freed = client.delete(f"/v1/event/{event_id}/vouchers/{v1}/assign", headers=organizer.headers)
    assert freed.status_code == 200 and freed.json()["hacker_id"] is None
    assert client.put(f"/v1/event/{event_id}/vouchers/{v2}/assign/{code}", headers=organizer.headers).status_code == 200
    assert client.get(f"/v1/event/{event_id}/is_participant/{hacker.id}", headers=organizer.headers).json() is True


def test_voucher_is_scoped_to_its_event_and_needs_accepted_hacker(client, create_user, create_event, accept, engine):
    organizer, accepted, rejected = create_user(role="organizer"), create_user(), create_user()
    event_id, other_event = create_event([accepted, rejected]), create_event()
    accept(organizer, event_id, accepted)
    voucher = client.post(f"/v1/event/{other_event}/vouchers/generate", headers=organizer.headers, json={"count": 1}).json()["vouchers"][0]["code"]
    assert client.put(f"/v1/event/{event_id}/vouchers/{voucher}/assign/{user_code(engine, accepted)}", headers=organizer.headers).status_code == 404
    own = client.post(f"/v1/event/{event_id}/vouchers/generate", headers=organizer.headers, json={"count": 1}).json()["vouchers"][0]["code"]
    assert client.put(f"/v1/event/{event_id}/vouchers/{own}/assign/{user_code(engine, rejected)}", headers=organizer.headers).status_code == 400
    assert client.put(f"/v1/event/{event_id}/vouchers/{own}/assign/UNKNOWN", headers=organizer.headers).status_code == 404
