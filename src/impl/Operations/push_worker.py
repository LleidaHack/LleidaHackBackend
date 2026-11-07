"""Run separately: uv run python -m src.impl.Operations.push_worker."""

import json
import logging
import os
import time
from datetime import UTC, datetime

from pywebpush import WebPushException, webpush
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src import imports  # noqa: F401
from src.configuration.Settings import settings
from src.impl.Operations.model import PushDelivery, PushSubscription
from src.impl.Operations.push_payload import compact_push_payload

logger = logging.getLogger("push_worker")


def deliver_one(engine):
    """Deliver the oldest pending push, committing per delivery.

    Only one row is locked at a time, and only for a single webpush call, so
    withdrawing an alert (which updates these rows under the event lock) never
    waits behind a whole batch of slow network calls.
    """
    with Session(engine) as session:
        delivery = (
            session.query(PushDelivery)
            .filter_by(state="pending")
            .order_by(PushDelivery.id)
            .with_for_update(skip_locked=True)
            .limit(1)
            .one_or_none()
        )
        if delivery is None:
            return False
        subscription = session.get(PushSubscription, delivery.subscription_id)
        if subscription is None or datetime.fromisoformat(
            delivery.payload["expires_at"]
        ) <= datetime.now(UTC):
            delivery.state = "expired"
            session.commit()
            return True
        delivery.attempts += 1
        try:
            webpush(
                subscription_info=subscription.subscription,
                data=json.dumps(compact_push_payload(delivery.payload)),
                vapid_private_key=os.environ["VAPID_PRIVATE_KEY"],
                vapid_claims={"sub": os.environ["VAPID_SUBJECT"]},
                timeout=10,
            )
            delivery.state = "sent"
        except WebPushException as exc:
            status = exc.response.status_code if exc.response is not None else 0
            if status in (404, 410) or delivery.attempts >= 5:
                delivery.state = "failed"
        except (OSError, ValueError):
            if delivery.attempts >= 5:
                delivery.state = "failed"
        session.commit()
        return True


def deliver_batch(engine, limit=200):
    """Drain up to ``limit`` pending deliveries; returns how many were handled."""
    handled = 0
    while handled < limit and deliver_one(engine):
        handled += 1
    return handled


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for key in ("VAPID_PRIVATE_KEY", "VAPID_SUBJECT"):
        if not os.getenv(key):
            raise SystemExit(f"Missing {key}")
    engine = create_engine(settings.database.url, pool_pre_ping=True)
    while True:
        try:
            # Keep draining without sleeping while there is a backlog.
            if deliver_batch(engine):
                continue
        except Exception:
            logger.exception("Push worker iteration failed; retrying later")
        time.sleep(2)
