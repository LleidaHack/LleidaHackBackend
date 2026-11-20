from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session

from src.impl.Event.model import HackerRejected
from src.impl.Mail.client import MailClient
from src.impl.Mail.internall_templates import InternalTemplate


@pytest.fixture
def rejection_mail(client, monkeypatch, engine):
    created, sent, templates = [], [], []

    def create(self, mail):
        created.append(mail)
        return SimpleNamespace(id=len(created))

    def send(self, mail_id):
        mail = created[mail_id - 1]
        with Session(engine) as session:
            assert (
                session.query(HackerRejected)
                .filter_by(user_id=int(mail.receiver_id))
                .count()
                == 1
            )
        sent.append(mail_id)

    monkeypatch.setattr(MailClient, "create_mail", create)
    monkeypatch.setattr(MailClient, "send_mail_by_id", send)
    monkeypatch.setattr(
        MailClient,
        "get_internall_template_id",
        lambda self, template: templates.append(template) or 123,
    )
    return created, sent, templates


def test_reject_sends_correct_mail_once(
    client, create_user, create_event, rejection_mail
):
    organizer = create_user(role="organizer")
    hacker = create_user(name="Laia, <Test>")
    event_id = create_event([hacker], name="HackEPS & friends")
    path = f"/v1/event/{event_id}/reject/{hacker.id}"
    response = client.put(path, headers=organizer.headers)
    assert response.status_code == 200, response.text
    created, sent, templates = rejection_mail
    assert templates == [InternalTemplate.EVENT_HACKER_REJECTED]
    assert sent == [1]
    assert created[0].receiver_mail == hacker.email
    assert created[0].template_id == 123
    assert created[0].fields == "Laia&#44; &lt;Test&gt;,HackEPS &amp; friends"
    assert created[0].subject == "Sobre la teva inscripció · HackEPS"
    assert client.put(path, headers=organizer.headers).status_code >= 400
    assert len(created) == 1


def test_group_reject_sends_only_to_new_rejections(
    client, create_user, create_event, create_group, engine, rejection_mail
):
    from src.impl.Event.model import HackerAccepted

    organizer = create_user(role="organizer")
    accepted, rejected, pending = create_user(), create_user(), create_user()
    event_id = create_event([accepted, rejected, pending])
    group = create_group(event_id, [accepted, rejected, pending])
    with Session(engine) as session:
        session.add(HackerAccepted(user_id=accepted.id, event_id=event_id))
        session.add(HackerRejected(user_id=rejected.id, event_id=event_id))
        session.commit()
    path = f"/v1/event/{event_id}/rejectgroup/{group.id}"
    for _ in range(2):
        response = client.put(path, headers=organizer.headers)
        assert response.status_code == 200, response.text
    created, sent, _ = rejection_mail
    assert [mail.receiver_mail for mail in created] == [pending.email]
    assert sent == [1]


def test_invalid_rejections_never_create_mail(
    client, create_user, create_event, rejection_mail
):
    organizer, hacker, outsider = (
        create_user(role="organizer"),
        create_user(),
        create_user(),
    )
    event_id = create_event([hacker])
    assert (
        client.put(
            f"/v1/event/{event_id}/reject/{hacker.id}", headers=hacker.headers
        ).status_code
        >= 400
    )
    assert (
        client.put(
            f"/v1/event/{event_id}/reject/{outsider.id}", headers=organizer.headers
        ).status_code
        >= 400
    )
    archived = create_event([hacker], archived=True)
    assert (
        client.put(
            f"/v1/event/{archived}/reject/{hacker.id}", headers=organizer.headers
        ).status_code
        >= 400
    )
    assert rejection_mail == ([], [], [])


def test_mail_creation_failure_preserves_pending_status(
    client, create_user, create_event, engine, rejection_mail, monkeypatch
):
    from src.error.MailClientException import MailClientException

    organizer, hacker = create_user(role="organizer"), create_user()
    event_id = create_event([hacker])

    def fail(self, mail):
        raise MailClientException("Mail service unavailable")

    monkeypatch.setattr(MailClient, "create_mail", fail)
    response = client.put(
        f"/v1/event/{event_id}/reject/{hacker.id}", headers=organizer.headers
    )
    assert response.status_code >= 400
    with Session(engine) as session:
        assert (
            session.query(HackerRejected)
            .filter_by(user_id=hacker.id, event_id=event_id)
            .count()
            == 0
        )
    assert rejection_mail[1] == []
