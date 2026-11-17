from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session


@pytest.fixture
def mail_delivery(client, monkeypatch):
    from src.impl.Mail.client import MailClient

    state = {"sent": False}
    create = Mock(return_value=SimpleNamespace(id=51))
    send = Mock(side_effect=lambda mail_id: state.update(sent=True))
    monkeypatch.setattr(MailClient, "create_mail", create)
    monkeypatch.setattr(MailClient, "send_mail_by_id", send)
    monkeypatch.setattr(MailClient, "is_mail_sent", lambda self, mail_id: state["sent"])
    return state, create, send


def confirmed(engine, user, event_id):
    from src.impl.Event.model import HackerAccepted, HackerRegistration

    with Session(engine) as session:
        session.add(HackerAccepted(user_id=user.id, event_id=event_id))
        session.get(HackerRegistration, (user.id, event_id)).confirmed_assistance = True
        session.commit()


def test_persistent_release_queue(
    client, create_user, create_event, engine, mail_delivery
):
    from src.impl.Event.release_queue import deliver_one
    from src.impl.Mail.client import MailClient

    actor, first, second, other = (
        create_user(role="organizer"),
        create_user(),
        create_user(),
        create_user(),
    )
    event_id = create_event([first, second, other])
    confirmed(engine, first, event_id)
    confirmed(engine, second, event_id)
    path = f"/v1/event/{event_id}/release-reminders"
    assert client.post(path, headers=other.headers).status_code >= 400
    assert client.post(path, headers=actor.headers).json() == {"registered": 2}
    assert client.post(path, headers=actor.headers).json() == {"registered": 0}
    state, _, send = mail_delivery
    send.side_effect = TimeoutError()
    assert deliver_one(engine, MailClient())
    send.side_effect = lambda _: state.update(sent=True)
    assert deliver_one(engine, MailClient())
    assert not deliver_one(engine, MailClient())
    assert client.get(path, headers=actor.headers).json() == {
        "pending": 0,
        "queued": 0,
        "checking": [first.id],
    }
    assert client.post(path, headers=actor.headers).json() == {"registered": 0}
    assert send.call_count == 2


def test_reminder_is_tracked_once_and_link_cancels(
    client, create_user, create_event, engine, mail_delivery
):
    from src.impl.Event.model import HackerRegistration
    from src.impl.User.model import User

    organizer, user = create_user(role="organizer"), create_user()
    event_id = create_event([user])
    confirmed(engine, user, event_id)
    _, create, send = mail_delivery
    path = f"/v1/event/{event_id}/release-reminder/{user.id}"
    first = client.post(path, headers=organizer.headers)
    assert first.status_code == 200, first.text
    assert first.json()["sent_at"]
    second = client.post(path, headers=organizer.headers)
    assert second.status_code == 200, second.text
    assert second.json()["already_sent"] is True
    assert second.json()["sent_at"] == first.json()["sent_at"]
    assert create.call_count == send.call_count == 1
    mail = create.call_args.args[0]
    with Session(engine) as session:
        registration = session.get(HackerRegistration, (user.id, event_id))
        token = registration.confirm_assistance_token
        assert mail.fields == f"{session.get(User, user.id).name},Test Event,{token}"
        assert registration.release_reminder_mail_id == 51
    listing = client.get(
        f"/v1/event/{event_id}/hackers_participants_list", headers=organizer.headers
    )
    assert (
        listing.json()["participants"][0]["release_reminder_sent_at"]
        == first.json()["sent_at"]
    )
    assert (
        client.post(
            "/v1/event/cancel_assistance/", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 200
    )


@pytest.mark.parametrize("delivered", [False, True])
def test_queue_only_checks_previous_mail(
    client, create_user, create_event, engine, mail_delivery, delivered
):
    from src.impl.Event.model import HackerRegistration
    from src.impl.Event.release_queue import deliver_one
    from src.impl.Mail.client import MailClient

    organizer, user = create_user(role="organizer"), create_user()
    event_id = create_event([user])
    confirmed(engine, user, event_id)
    with Session(engine) as session:
        session.get(
            HackerRegistration, (user.id, event_id)
        ).release_reminder_mail_id = 51
        session.commit()
    state, create, send = mail_delivery
    state["sent"] = delivered
    path = f"/v1/event/{event_id}/release-reminders"
    assert client.post(path, headers=organizer.headers).status_code == 202
    assert deliver_one(engine, MailClient())
    assert not deliver_one(engine, MailClient())
    assert client.get(path, headers=organizer.headers).json()["checking"] == (
        [] if delivered else [user.id]
    )
    create.assert_not_called()
    send.assert_not_called()


@pytest.mark.parametrize("delivered", [False, True])
def test_retry_reuses_mail_and_reconciles_ambiguous_delivery(
    client, create_user, create_event, engine, mail_delivery, delivered
):
    from src.impl.Event.model import HackerRegistration

    organizer, user = create_user(role="organizer"), create_user()
    event_id = create_event([user])
    confirmed(engine, user, event_id)
    state, create, send = mail_delivery

    def timeout(mail_id):
        state["sent"] = delivered
        raise TimeoutError("Response lost")

    send.side_effect = timeout
    path = f"/v1/event/{event_id}/release-reminder/{user.id}"
    response = client.post(path, headers=organizer.headers)
    assert response.status_code == 200 if delivered else response.status_code >= 400
    with Session(engine) as session:
        registration = session.get(HackerRegistration, (user.id, event_id))
        assert (registration.release_reminder_sent_at is not None) == delivered
        assert registration.release_reminder_mail_id == 51
        token = registration.confirm_assistance_token
    send.side_effect = lambda mail_id: state.update(sent=True)
    retry = client.post(path, headers=organizer.headers)
    assert retry.status_code == 200, retry.text
    assert create.call_count == 1
    assert send.call_count == (1 if delivered else 2)
    with Session(engine) as session:
        assert (
            session.get(
                HackerRegistration, (user.id, event_id)
            ).confirm_assistance_token
            == token
        )


@pytest.mark.parametrize(
    "reason", ["unconfirmed", "not_accepted", "cancelled", "archived", "unauthorized"]
)
def test_ineligible_recipient_does_not_receive_mail(
    client, create_user, create_event, engine, mail_delivery, reason
):
    from datetime import UTC, datetime

    from src.impl.Event.model import Event, HackerAccepted, HackerRegistration

    organizer, user = create_user(role="organizer"), create_user()
    event_id = create_event([user])
    confirmed(engine, user, event_id)
    with Session(engine) as session:
        registration = session.get(HackerRegistration, (user.id, event_id))
        if reason == "unconfirmed":
            registration.confirmed_assistance = False
        elif reason == "not_accepted":
            session.delete(session.get(HackerAccepted, (user.id, event_id)))
        elif reason == "cancelled":
            registration.cancelled_at = datetime.now(UTC).replace(tzinfo=None)
        elif reason == "archived":
            session.get(Event, event_id).archived = True
        session.commit()
    response = client.post(
        f"/v1/event/{event_id}/release-reminder/{user.id}",
        headers=user.headers if reason == "unauthorized" else organizer.headers,
    )
    assert response.status_code in (400, 401, 403), response.text
    assert mail_delivery[1].call_count == 0
    assert mail_delivery[2].call_count == 0


def test_unsuccessful_mail_response_is_not_marked_sent(
    client, create_user, create_event, engine, mail_delivery
):
    from src.impl.Event.model import HackerRegistration

    organizer, user = create_user(role="organizer"), create_user()
    event_id = create_event([user])
    confirmed(engine, user, event_id)
    mail_delivery[2].side_effect = None
    mail_delivery[2].return_value = SimpleNamespace(status_code=500)
    response = client.post(
        f"/v1/event/{event_id}/release-reminder/{user.id}", headers=organizer.headers
    )
    assert response.status_code >= 400
    with Session(engine) as session:
        assert (
            session.get(
                HackerRegistration, (user.id, event_id)
            ).release_reminder_sent_at
            is None
        )
