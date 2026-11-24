from sqlalchemy.orm import Session


def test_delete_rejected_hacker_with_notes_and_audit(
    client, create_user, create_event, engine
):
    from src.impl.Event.model import (
        EventAuditLog,
        EventParticipantNote,
        HackerRegistration,
        HackerRejected,
    )
    from src.impl.User.model import User

    organizer, hacker = create_user(role="organizer"), create_user()
    event = create_event([hacker])
    with Session(engine) as session:
        session.add(HackerRejected(user_id=hacker.id, event_id=event))
        session.add(
            EventParticipantNote(
                event_id=event, hacker_id=hacker.id, author_id=organizer.id, body="x"
            )
        )
        session.add(
            EventAuditLog(
                event_id=event,
                actor_id=organizer.id,
                action="reject",
                target_id=hacker.id,
            )
        )
        session.commit()
    response = client.delete(f"/v1/hacker/{hacker.id}", headers=organizer.headers)
    assert response.status_code == 200, response.text
    with Session(engine) as session:
        assert session.get(User, hacker.id) is None
        assert session.get(HackerRegistration, (hacker.id, event)) is None
        assert session.query(HackerRejected).filter_by(user_id=hacker.id).count() == 0
        log = session.query(EventAuditLog).filter_by(event_id=event).one()
        assert log.target_id is None and log.actor_id == organizer.id


def test_delete_refuses_accounts_with_ledger_history(client, create_user, engine):
    from src.impl.Operations.model import AccessRoleAudit
    from src.impl.User.model import User

    organizer, hacker = create_user(role="organizer"), create_user()
    with Session(engine) as session:
        session.add(
            AccessRoleAudit(
                actor_id=organizer.id,
                user_id=hacker.id,
                previous_role="hacker",
                new_role="mentor",
                reason="test",
            )
        )
        session.commit()
    response = client.delete(f"/v1/hacker/{hacker.id}", headers=organizer.headers)
    assert response.status_code == 400, response.text
    assert "cannot be deleted" in response.text
    with Session(engine) as session:
        assert session.get(User, hacker.id) is not None
