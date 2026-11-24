from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session


@pytest.fixture
def discord_mails(monkeypatch):
    from src.impl.Mail.client import MailClient

    created, templates = [], []

    def create(self, mail):
        created.append(mail)
        return SimpleNamespace(id=len(created))

    monkeypatch.setattr(MailClient, "create_mail", create)
    monkeypatch.setattr(
        MailClient,
        "get_internall_template_id",
        lambda self, template: templates.append(template) or 77,
    )
    return created, templates


def configure_discord(engine, event_id, url):
    from src.impl.Operations.model import EventOperations

    with Session(engine) as session:
        row = session.get(EventOperations, event_id)
        if row is None:
            row = EventOperations(event_id=event_id, version=0, config={})
            session.add(row)
        row.config = {**(row.config or {}), "slack_url": url}
        session.commit()


def confirm(client, engine, organizer, event_id, user, confirmed=True):
    from src.impl.Event.model import HackerRegistration

    response = client.put(
        f"/v1/event/{event_id}/accept/{user.id}", headers=organizer.headers
    )
    assert response.status_code == 200, response.text
    with Session(engine) as session:
        session.get(
            HackerRegistration, (user.id, event_id)
        ).confirmed_assistance = confirmed
        session.commit()


def test_discord_invite_goes_only_to_confirmed_hackers(
    client, create_user, create_event, engine, discord_mails
):
    from src.impl.Event.service import EventService
    from src.impl.Mail.internall_templates import InternalTemplate

    organizer = create_user(role="organizer")
    confirmed = create_user(name="Laia, <Test>")
    unconfirmed, pending = create_user(), create_user()
    event_id = create_event([confirmed, unconfirmed, pending], name="HackEPS & co")
    confirm(client, engine, organizer, event_id, confirmed)
    confirm(client, engine, organizer, event_id, unconfirmed, confirmed=False)
    path = f"/v1/event/{event_id}/discord-invite"

    assert client.post(path, headers=organizer.headers).status_code == 400
    assert client.get(path, headers=confirmed.headers).status_code in (401, 403)
    assert client.post(path, headers=confirmed.headers).status_code in (401, 403)

    configure_discord(engine, event_id, "https://discord.gg/hackeps")
    status = client.get(path, headers=organizer.headers).json()
    assert status["discord_url"] == "https://discord.gg/hackeps"
    assert status["recipients"] == 1

    created, templates = discord_mails
    created.clear()
    templates.clear()
    EventService().send_discord_mails_background(
        event_id, "https://discord.gg/hackeps", delay=0
    )
    assert templates == [InternalTemplate.EVENT_DISCORD_INVITE]
    assert [mail.receiver_mail for mail in created] == [confirmed.email]
    assert created[0].template_id == 77
    assert created[0].fields == (
        "Laia&#44; &lt;Test&gt;,HackEPS &amp; co,https://discord.gg/hackeps"
    )
    assert created[0].subject == "Uneix-te al Discord de la HackEPS"

    response = client.post(path, headers=organizer.headers)
    assert response.status_code == 200 and response.json()["scheduled"] is True
