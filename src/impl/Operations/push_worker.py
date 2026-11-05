"""Run separately: uv run python -m src.impl.Operations.push_worker."""

import json
import os
import time
from datetime import UTC, datetime

from pywebpush import WebPushException, webpush
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src import imports  # noqa: F401
from src.configuration.Settings import settings
from src.impl.Operations.model import PushDelivery, PushSubscription


def deliver_batch(engine):
    with Session(engine) as session:
        deliveries = (
            session.query(PushDelivery)
            .filter_by(state="pending")
            .with_for_update(skip_locked=True)
            .limit(20)
            .all()
        )
        for delivery in deliveries:
            subscription = session.get(PushSubscription, delivery.subscription_id)
            if datetime.fromisoformat(delivery.payload["expires_at"]) <= datetime.now(
                UTC
            ):
                delivery.state = "expired"
                continue
            delivery.attempts += 1
            try:
                webpush(
                    subscription_info=subscription.subscription,
                    data=json.dumps(delivery.payload),
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


if __name__ == "__main__":
    for key in ("VAPID_PRIVATE_KEY", "VAPID_SUBJECT"):
        if not os.getenv(key):
            raise SystemExit(f"Missing {key}")
    engine = create_engine(settings.database.url)
    while True:
        deliver_batch(engine)
        time.sleep(15)
