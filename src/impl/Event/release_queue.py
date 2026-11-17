import logging
import time

from sqlalchemy import case, create_engine
from sqlalchemy.orm import Session

from src.error.InvalidDataException import InvalidDataException
from src.impl.Event.model import HackerAccepted, HackerRegistration
from src.impl.Event.service import EventService
from src.impl.Mail.client import MailClient

logger = logging.getLogger(__name__)


def pending(session, event_id):
    return (
        session.query(HackerRegistration)
        .filter_by(
            event_id=event_id,
            confirmed_assistance=True,
            cancelled_at=None,
            release_reminder_sent_at=None,
            release_queue_state=None,
        )
        .filter(
            HackerRegistration.user_id.in_(
                session.query(HackerAccepted.user_id).filter_by(event_id=event_id)
            )
        )
    )


def enqueue(session, event_id, actor):
    count = pending(session, event_id).update(
        {
            HackerRegistration.release_queue_state: case(
                (HackerRegistration.release_reminder_mail_id.is_not(None), "verify"),
                else_="queued",
            ),
            HackerRegistration.release_queue_actor: actor or None,
        },
        synchronize_session=False,
    )
    session.commit()
    return {"registered": count}


def queue_status(session, event_id):
    rows = (
        session.query(
            HackerRegistration.user_id, HackerRegistration.release_queue_state
        )
        .filter_by(event_id=event_id, release_reminder_sent_at=None)
        .filter(HackerRegistration.release_queue_state.is_not(None))
        .all()
    )
    return {
        "pending": pending(session, event_id).count(),
        "queued": sum(state in {"queued", "verify"} for _, state in rows),
        "checking": [uid for uid, state in rows if state == "review"],
    }


def deliver_one(engine, client):
    with Session(engine) as session:
        row = (
            session.query(HackerRegistration)
            .filter(HackerRegistration.release_queue_state.in_(("queued", "verify")))
            .order_by(HackerRegistration.event_id, HackerRegistration.user_id)
            .with_for_update(skip_locked=True)
            .first()
        )
        if row is None:
            return False
        event_id, user_id, actor = row.event_id, row.user_id, row.release_queue_actor
        verify_only = row.release_queue_state == "verify"
        row.release_queue_state = "review"
        session.commit()
        try:
            EventService.deliver_release_reminder(
                session, event_id, user_id, actor, client, verify_only=verify_only
            )
        except InvalidDataException:
            session.rollback()
            row.release_queue_state = None
            session.commit()
        except Exception as error:  # noqa: BLE001
            session.rollback()
            logger.warning(
                "Release reminder requires review: event=%s user=%s error=%s",
                event_id,
                user_id,
                type(error).__name__,
            )
        return True


if __name__ == "__main__":
    from src import imports  # noqa: F401
    from src.configuration.Settings import settings

    engine = create_engine(settings.database.url, pool_pre_ping=True)
    client = MailClient()
    while True:
        try:
            if deliver_one(engine, client):
                continue
        except Exception:
            logger.exception("Release reminder worker unavailable")
        time.sleep(2)
