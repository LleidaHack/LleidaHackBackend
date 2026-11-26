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


def test_mentor_discord_link_is_private_and_only_for_active_mentors(
    client, create_user, create_event, engine, discord_mails
):
    from src.impl.Event.service import EventService
    from src.impl.Mail.internall_templates import InternalTemplate
    from src.impl.Operations.model import EventOperations

    organizer, hacker = create_user(role="organizer"), create_user()
    event_id = create_event([hacker])
    confirm(client, engine, organizer, event_id, hacker)
    base = f"/v1/operations/{event_id}/mentors"
    active = client.post(
        base,
        headers=organizer.headers,
        json={"name": "Mentor Actiu", "email": "actiu@example.test"},
    ).json()["id"]
    inactive = client.post(
        base,
        headers=organizer.headers,
        json={"name": "Mentor Inactiu", "email": "inactiu@example.test"},
    ).json()["id"]
    assert (
        client.patch(
            f"{base}/{inactive}", headers=organizer.headers, json={"active": False}
        ).status_code
        == 200
    )
    path = f"/v1/event/{event_id}/discord-invite"
    configure_discord(engine, event_id, "https://discord.gg/hackeps")
    assert (
        client.post(path + "?audience=mentor", headers=organizer.headers).status_code
        == 400
    )
    with Session(engine) as session:
        row = session.get(EventOperations, event_id)
        row.config = {**row.config, "mentor_discord_url": "https://discord.gg/mentors"}
        session.commit()

    public = client.get(f"/v1/operations/{event_id}/public").json()
    assert "mentor_discord_url" not in str(public)
    status = client.get(path, headers=organizer.headers).json()
    assert status["mentor_discord_url"] == "https://discord.gg/mentors"
    assert (status["recipients"], status["mentor_recipients"]) == (1, 1)

    created, templates = discord_mails
    created.clear()
    templates.clear()
    EventService().send_discord_mails_background(
        event_id, "https://discord.gg/mentors", delay=0, audience="mentor"
    )
    assert templates == [InternalTemplate.EVENT_DISCORD_INVITE_MENTOR]
    assert [mail.receiver_mail for mail in created] == ["actiu@example.test"]
    assert int(created[0].receiver_id) == active
    assert created[0].fields.endswith(",https://discord.gg/mentors")
