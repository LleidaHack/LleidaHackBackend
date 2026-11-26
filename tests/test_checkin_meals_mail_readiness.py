from contextlib import contextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session


@pytest.fixture
def mails(client, monkeypatch):
    """Capture created and sent mails (the mail client is mocked in conftest)."""
    from src.impl.Mail.client import MailClient

    created, sent = [], []

    def create_mail(self, mail):
        created.append(mail)
        return SimpleNamespace(id=len(created))

    monkeypatch.setattr(MailClient, "create_mail", create_mail)
    monkeypatch.setattr(MailClient, "send_mail_by_id", lambda self, i: sent.append(i))
    return SimpleNamespace(created=created, sent=sent)


@pytest.fixture
def sleeps(monkeypatch):
    """Record bulk-mail pacing with the production minimum interval."""
    from src.utils import bulk_mail

    recorded = []
    monkeypatch.setattr(bulk_mail, "BULK_MAIL_MIN_INTERVAL", 2.0)
    monkeypatch.setattr(bulk_mail, "time", SimpleNamespace(sleep=recorded.append))
    return recorded


def seed_accepted(engine, event_id, users, confirmed=True):
    from src.impl.Event.model import HackerAccepted, HackerRegistration

    with Session(engine) as session:
        for user in users:
            session.add(HackerAccepted(user_id=user.id, event_id=event_id))
            registration = session.get(HackerRegistration, (user.id, event_id))
            registration.confirmed_assistance = confirmed
        session.commit()


def user_code(engine, user):
    from src.impl.User.model import User

    with Session(engine) as session:
        return session.get(User, user.id).code


def test_staff_can_scan_their_badge_for_meals_only(
    client, create_user, create_event, engine
):
    admin, staff = create_user(role="organizer"), create_user(role="lleidahacker")
    event_id = create_event()
    badge = client.post(
        f"/v1/event/{event_id}/vouchers/generate",
        headers=admin.headers,
        json={"count": 1},
    ).json()["vouchers"][0]["code"]
    assigned = client.put(
        f"/v1/event/{event_id}/vouchers/{badge}/assign/{user_code(engine, staff)}",
        headers=admin.headers,
    )
    assert assigned.status_code == 200, assigned.text
    meal = client.post(
        "/v1/meal/",
        headers=admin.headers,
        json={"name": "Lunch", "description": "", "event_id": event_id},
    ).json()["id"]

    def scan(kind="meal"):
        return client.post(
            f"/v1/operations/{event_id}/scan",
            headers=staff.headers,
            json={
                "operation_id": str(uuid4()),
                "kind": kind,
                "code": badge,
                "target": str(meal),
                "round": 1,
            },
        )

    first = scan()
    assert first.status_code == 200, first.text
    assert first.json()["user_id"] == staff.id
    assert scan().status_code == 409  # one meal per round, like everyone else
    for kind in ("activity", "checkin"):
        assert scan(kind).status_code == 403


def test_accepting_a_rejected_hacker_clears_the_rejection(
    client, create_user, create_event, engine, mails
):
    from src.impl.Event.model import HackerAccepted, HackerRejected

    organizer, hacker = create_user(role="organizer"), create_user()
    event_id = create_event([hacker])
    rejected = client.put(
        f"/v1/event/{event_id}/reject/{hacker.id}", headers=organizer.headers
    )
    assert rejected.status_code == 200, rejected.text
    accepted = client.put(
        f"/v1/event/{event_id}/accept/{hacker.id}", headers=organizer.headers
    )
    assert accepted.status_code == 200, accepted.text
    with Session(engine) as session:
        assert session.get(HackerAccepted, (hacker.id, event_id)) is not None
        assert session.get(HackerRejected, (hacker.id, event_id)) is None


def test_every_bulk_sender_waits_between_mails(
    client, create_user, create_event, engine, mails, sleeps
):
    from src.impl.Event.service import EventService

    confirmed = [create_user(), create_user(), create_user()]
    unconfirmed = [create_user(), create_user()]
    event_id = create_event(confirmed)
    reminder_event = create_event(unconfirmed)
    seed_accepted(engine, event_id, confirmed)
    seed_accepted(engine, reminder_event, unconfirmed, confirmed=False)
    service = EventService()

    service.send_ticket_mails_background(event_id)
    assert len(mails.sent) == 3 and sleeps == [2.0, 2.0]
    sleeps.clear()
    # A larger requested delay wins over the minimum.
    service.send_ticket_mails_background(event_id, force=True, delay=5.0)
    assert sleeps == [5.0, 5.0]
    for job in (
        lambda: service.send_discord_mails_background(event_id, "https://x.test", 0),
        lambda: service.send_slack_mail_background(event_id, "https://x.test", 0),
    ):
        sleeps.clear()
        job()
        assert sleeps == [2.0, 2.0]
    sleeps.clear()
    service.send_reminder_mails_background(reminder_event)
    assert sleeps == [2.0]


def test_release_queue_worker_waits_between_mails(monkeypatch, sleeps):
    from src.impl.Event import release_queue

    results = iter([True, True, False])
    monkeypatch.setattr(release_queue, "deliver_one", lambda e, c: next(results))
    idle = []
    monkeypatch.setattr(release_queue, "time", SimpleNamespace(sleep=idle.append))
    rounds = iter(range(3))
    release_queue.run(None, None, lambda: next(rounds, None) is not None)
    assert sleeps == [2.0, 2.0]
    assert idle == [2]


@contextmanager
def other_worker_lock(engine, job, event_id):
    """Hold a job lock the way a job on another gunicorn worker would."""
    from src.utils.bulk_mail import BULK_JOB_LOCK_KEYS

    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT pg_try_advisory_lock(:key, :event)"),
            {"key": BULK_JOB_LOCK_KEYS[job], "event": event_id},
        ).scalar()
        connection.commit()
        try:
            yield
        finally:
            connection.execute(text("SELECT pg_advisory_unlock_all()"))
            connection.commit()


@pytest.mark.parametrize(
    "job,path",
    [
        ("ticket", "/tickets/send"),
        ("reminder", "/send_reminder_mails/"),
        ("slack", "/send_slack_mail/?slackUrl=https://x.test"),
    ],
)
def test_bulk_job_running_on_another_worker_is_refused(
    client, create_user, create_event, engine, mails, job, path
):
    organizer, hacker = create_user(role="organizer"), create_user()
    event_id = create_event([hacker])
    seed_accepted(engine, event_id, [hacker], confirmed=job != "reminder")
    with other_worker_lock(engine, job, event_id):
        response = client.post(f"/v1/event/{event_id}{path}", headers=organizer.headers)
        assert response.status_code == 409, response.text
        assert mails.created == []
    response = client.post(f"/v1/event/{event_id}{path}", headers=organizer.headers)
    assert response.status_code == 200, response.text
    # The organizer is staff and also gets a ticket; the hacker must be mailed.
    assert str(hacker.id) in [mail.receiver_id for mail in mails.created]


def test_discord_invite_refused_while_running_elsewhere(
    client, create_user, create_event, engine, mails
):
    from src.impl.Operations.model import EventOperations

    organizer, hacker = create_user(role="organizer"), create_user()
    event_id = create_event([hacker])
    seed_accepted(engine, event_id, [hacker])
    with Session(engine) as session:
        session.add(
            EventOperations(event_id=event_id, config={"slack_url": "https://x.test"})
        )
        session.commit()
    path = f"/v1/event/{event_id}/discord-invite"
    with other_worker_lock(engine, "discord", event_id):
        assert client.post(path, headers=organizer.headers).status_code == 409
    assert client.post(path, headers=organizer.headers).status_code == 200
    assert len(mails.sent) == 1


def test_duplicate_job_on_another_worker_sends_nothing(
    client, create_user, create_event, engine, mails
):
    from src.impl.Event.service import EventService
    from src.utils.bulk_mail import bulk_job_running

    hacker = create_user()
    event_id = create_event([hacker])
    seed_accepted(engine, event_id, [hacker])
    with other_worker_lock(engine, "ticket", event_id):
        EventService().send_ticket_mails_background(event_id)
        assert mails.created == []

    # The lock is held while the job runs and released afterwards.
    held = []

    def send(self, mail_id):
        with Session(engine) as session:
            held.append(bulk_job_running(session, event_id, "ticket"))

    from src.impl.Mail.client import MailClient

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(MailClient, "send_mail_by_id", send)
        EventService().send_ticket_mails_background(event_id)
    assert held == [True]
    with Session(engine) as session:
        assert not bulk_job_running(session, event_id, "ticket")


def test_ticket_job_skips_recipients_sent_since_it_started(
    client, create_user, create_event, engine, mails, monkeypatch
):
    from src.impl.Event.model import HackerRegistration
    from src.impl.Event.service import EventService

    first, second = create_user(), create_user()
    event_id = create_event([first, second])
    seed_accepted(engine, event_id, [first, second])
    original = EventService._ticket_recipients

    def stale_recipients(session, event, *args):
        recipients = original(session, event, *args)
        # Another (resumed) job delivers the first ticket meanwhile.
        with Session(engine) as other:
            other.get(
                HackerRegistration, (first.id, event_id)
            ).ticket_sent_at = other.execute(text("SELECT LOCALTIMESTAMP")).scalar()
            other.commit()
        return recipients

    monkeypatch.setattr(
        EventService, "_ticket_recipients", staticmethod(stale_recipients)
    )
    service = EventService()
    service.send_ticket_mails_background(event_id)
    assert [mail.receiver_id for mail in mails.created] == [str(second.id)]
    progress = service.get_send_progress(event_id)
    assert (progress["total"], progress["sent"], progress["failed"]) == (1, 1, 0)
