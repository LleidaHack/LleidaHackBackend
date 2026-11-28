import pytest
from sqlalchemy.orm import Session


def invitation(engine, user, event_id, *, confirmed=False, legacy=False):
    from src.impl.Event.model import HackerAccepted, HackerRegistration
    from src.impl.User.model import User
    from src.utils.Token import AssistenceToken

    with Session(engine) as session:
        token = AssistenceToken(session.get(User, user.id), event_id).to_token()
        registration = session.get(HackerRegistration, (user.id, event_id))
        registration.confirm_assistance_token = "" if legacy else token
        registration.confirmed_assistance = confirmed
        session.add(HackerAccepted(user_id=user.id, event_id=event_id))
        session.commit()
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    "confirmed,legacy", [(False, False), (True, False), (True, True)]
)
def test_release_preserves_registration_and_updates_admin(
    client, create_user, create_event, engine, confirmed, legacy
):
    from src.impl.Event.model import EventAuditLog, HackerAccepted, HackerRegistration

    user, other = create_user(), create_user()
    organizer = create_user(role="organizer")
    event_id = create_event([user, other], max_participants=1)
    other_event = create_event([user])
    headers = invitation(engine, user, event_id, confirmed=confirmed, legacy=legacy)
    invitation(engine, user, other_event, confirmed=True)
    for _ in range(2):
        response = client.post("/v1/event/cancel_assistance/", headers=headers)
        assert response.status_code == 200, response.text
        assert response.json() == {"success": True}
    assert (
        client.get("/v1/event/confirm_assistance/", headers=headers).status_code == 400
    )
    with Session(engine) as session:
        registration = session.get(HackerRegistration, (user.id, event_id))
        assert registration.cancelled_at is not None
        assert registration.confirmed_assistance is False
        assert session.get(HackerAccepted, (user.id, event_id)) is None
        assert session.get(HackerAccepted, (user.id, other_event)) is not None
        assert (
            session.get(HackerRegistration, (other.id, event_id)).cancelled_at is None
        )
        assert (
            session.query(EventAuditLog).filter_by(action="cancel_assistance").count()
            == 1
        )
    response = client.get(
        f"/v1/event/{event_id}/hackers_participants_list", headers=organizer.headers
    )
    assert response.status_code == 200, response.text
    participants = {p["id"]: p for p in response.json()["participants"]}
    assert participants[user.id]["status"] == "cancelled"
    assert participants[user.id]["confirmed_assistance"] is False
    assert participants[other.id]["status"] == "pending"
    grouped = client.get(
        f"/v1/event/{event_id}/hackers_participants_grouped_list",
        headers=organizer.headers,
    )
    assert grouped.status_code == 200, grouped.text
    assert (
        next(p for p in grouped.json()["nogroup"] if p["id"] == user.id)["status"]
        == "cancelled"
    )
    pending = client.get(
        f"/v1/event/{event_id}/pendinggruped", headers=organizer.headers
    )
    assert pending.status_code == 200, pending.text
    assert user.id not in [p["id"] for p in pending.json()["nogroup"]]
    # An organizer cannot silently revive a voluntarily cancelled place.
    assert (
        client.put(
            f"/v1/event/{event_id}/accept/{user.id}", headers=organizer.headers
        ).status_code
        == 400
    )


def test_cancellation_requires_assistance_token_and_post(
    client, create_user, create_event, engine
):
    user = create_user()
    event_id = create_event([user])
    headers = invitation(engine, user, event_id)
    assert client.post("/v1/event/cancel_assistance/").status_code in (401, 403)
    assert (
        client.post("/v1/event/cancel_assistance/", headers=user.headers).status_code
        == 401
    )
    assert (
        client.post(
            "/v1/event/cancel_assistance/", headers={"Authorization": "Bearer invalid"}
        ).status_code
        == 401
    )
    assert (
        client.get("/v1/event/cancel_assistance/", headers=headers).status_code != 200
    )


@pytest.mark.parametrize("blocked", ["archived", "checked_in", "replaced_token"])
def test_invalid_cancellation_does_not_release_place(
    client, create_user, create_event, engine, blocked
):
    from src.impl.Event.model import (
        Event,
        HackerAccepted,
        HackerParticipation,
        HackerRegistration,
    )

    user = create_user()
    event_id = create_event([user])
    headers = invitation(engine, user, event_id, confirmed=True)
    with Session(engine) as session:
        if blocked == "archived":
            session.get(Event, event_id).archived = True
        elif blocked == "checked_in":
            session.add(HackerParticipation(user_id=user.id, event_id=event_id))
        else:
            session.get(
                HackerRegistration, (user.id, event_id)
            ).confirm_assistance_token = "replacement"
        session.commit()
    response = client.post("/v1/event/cancel_assistance/", headers=headers)
    assert response.status_code in (400, 401), response.text
    with Session(engine) as session:
        assert session.get(HackerAccepted, (user.id, event_id)) is not None
        assert session.get(HackerRegistration, (user.id, event_id)).cancelled_at is None


def test_releasing_place_allows_another_registration(
    client, create_user, create_event, engine
):
    owner, newcomer = create_user(), create_user()
    event_id = create_event([owner], max_participants=1)
    headers = invitation(engine, owner, event_id, confirmed=True)
    payload = {
        "shirt_size": "M",
        "food_restrictions": "",
        "studies": "Computing",
        "study_center": "UdL",
        "location": "Lleida",
        "how_did_you_meet_us": "Friends",
        "wants_credit": False,
        "update_user": False,
    }
    path = f"/v1/event/{event_id}/register/{newcomer.id}"
    before = client.put(path, json=payload, headers=newcomer.headers)
    assert before.status_code == 400, before.text
    assert "full" in before.text.lower()
    assert (
        client.post("/v1/event/cancel_assistance/", headers=headers).status_code == 200
    )
    after = client.put(path, json=payload, headers=newcomer.headers)
    assert after.status_code == 200, after.text


def test_organizer_can_reaccept_cancelled_place(
    client, create_user, create_event, engine
):
    from src.impl.Event.model import (
        EventAuditLog,
        HackerAccepted,
        HackerRegistration,
    )

    user, pending = create_user(), create_user()
    organizer = create_user(role="organizer")
    event_id = create_event([user, pending])
    headers = invitation(engine, user, event_id, confirmed=True)
    with Session(engine) as session:
        registration = session.get(HackerRegistration, (user.id, event_id))
        registration.release_reminder_sent_at = registration.registered_at
        registration.release_reminder_mail_id = 7
        session.commit()
    assert (
        client.post("/v1/event/cancel_assistance/", headers=headers).status_code == 200
    )
    reaccept = f"/v1/event/{event_id}/reaccept/{user.id}"
    # Only organizers, and only for cancelled places.
    assert client.put(reaccept, headers=user.headers).status_code in (401, 403)
    assert (
        client.put(
            f"/v1/event/{event_id}/reaccept/{pending.id}", headers=organizer.headers
        ).status_code
        == 400
    )
    response = client.put(reaccept, headers=organizer.headers)
    assert response.status_code == 200, response.text
    with Session(engine) as session:
        registration = session.get(HackerRegistration, (user.id, event_id))
        assert registration.cancelled_at is None
        assert registration.confirmed_assistance is False
        assert registration.release_reminder_sent_at is None
        assert registration.release_reminder_mail_id is None
        assert session.get(HackerAccepted, (user.id, event_id)) is not None
        assert session.query(EventAuditLog).filter_by(action="reaccept").count() == 1
        new_token = registration.confirm_assistance_token
    participants = {
        p["id"]: p
        for p in client.get(
            f"/v1/event/{event_id}/hackers_participants_list",
            headers=organizer.headers,
        ).json()["participants"]
    }
    assert participants[user.id]["status"] == "accepted"
    # The new acceptance mail's token confirms attendance again.
    confirmed = client.get(
        "/v1/event/confirm_assistance/",
        headers={"Authorization": f"Bearer {new_token}"},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert client.put(reaccept, headers=organizer.headers).status_code == 400, (
        "an accepted place cannot be re-accepted"
    )
