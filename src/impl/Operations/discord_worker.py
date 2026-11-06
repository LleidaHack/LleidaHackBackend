"""Webhook outbox worker: uv run python -m src.impl.Operations.discord_worker."""

import logging
import os
import re
import time
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import create_engine, or_, text
from sqlalchemy.orm import Session

from src import imports  # noqa: F401
from src.configuration.Settings import settings
from src.impl.Operations.discord_messages import discord_message, webhook_url
from src.impl.Operations.model import DiscordDelivery

logger = logging.getLogger(__name__)
# HTTP client debug/info logs include token-bearing webhook URLs.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def deliver_one(engine, event_id, post=httpx.post):
    url = webhook_url(event_id)
    if not url:
        return False
    now = datetime.now(UTC)
    with Session(engine) as session:
        # Serialize sends for this event/webhook, including rate-limit backoff updates.
        if not session.execute(
            text("SELECT pg_try_advisory_xact_lock(76430, :event)"), {"event": event_id}
        ).scalar():
            return False
        row = (
            session.query(DiscordDelivery)
            .filter(
                DiscordDelivery.event_id == event_id,
                DiscordDelivery.state == "pending",
                or_(
                    DiscordDelivery.lease_until.is_(None),
                    DiscordDelivery.lease_until <= now,
                ),
            )
            .order_by(DiscordDelivery.id)
            .with_for_update(skip_locked=True)
            .first()
        )
        if not row:
            return False
        if datetime.fromisoformat(row.payload["expires_at"]) <= now:
            row.state = "expired"
            session.commit()
            return True
        if row.attempts >= 5:
            row.state = "failed"
            session.commit()
            return True
        row.attempts += 1
        try:
            # wait=true returns a message ID only once Discord has persisted the post.
            response = post(
                url,
                params={"wait": "true"},
                json=discord_message(row.payload),
                timeout=10,
                follow_redirects=False,
            )
            if response.status_code == 200:
                message_id = str(response.json().get("id", ""))
                if not re.fullmatch(r"[0-9]{1,30}", message_id):
                    row.state, row.error = (
                        "failed",
                        "Discord response missing message ID; verify channel before resending",
                    )
                else:
                    row.state, row.message_id, row.error = "sent", message_id, None
            elif response.status_code == 429:
                try:
                    delay = float(response.json().get("retry_after", 5))
                    delay = max(1, min(delay, 86400))
                except (ValueError, TypeError):
                    delay = 5
                retry_at = now + timedelta(seconds=delay + 1)
                session.query(DiscordDelivery).filter_by(
                    event_id=event_id, state="pending"
                ).update(
                    {DiscordDelivery.lease_until: retry_at}, synchronize_session=False
                )
                row.lease_until = retry_at
                row.error = "Discord rate limit; retry scheduled"
            elif response.status_code >= 500:
                row.lease_until = now + timedelta(seconds=15 * 2 ** (row.attempts - 1))
                row.error = "Discord temporarily unavailable; retry scheduled"
            else:
                row.state, row.error = (
                    "failed",
                    f"Discord rejected delivery (HTTP {response.status_code})",
                )
        except httpx.ConnectError:
            row.lease_until = now + timedelta(seconds=15 * 2 ** (row.attempts - 1))
            row.error = "Could not connect to Discord; retry scheduled"
        except (httpx.HTTPError, ValueError, KeyError):
            # A read timeout can occur after Discord accepted the message. Do not
            # automatically retry an ambiguous result and spam the channel.
            row.state, row.error = (
                "failed",
                "Delivery unconfirmed; verify channel before resending",
            )
        if row.state == "pending" and row.attempts >= 5:
            row.state = "failed"
        session.commit()
        return True


if __name__ == "__main__":
    event_id = int(os.getenv("DISCORD_WEBHOOK_EVENT_ID", "0"))
    if not webhook_url(event_id):
        raise SystemExit(
            "Configure a valid DISCORD_WEBHOOK_URL and DISCORD_WEBHOOK_EVENT_ID"
        )
    engine = create_engine(settings.database.url)
    while True:
        try:
            for _ in range(20):
                if not deliver_one(engine, event_id):
                    break
        except Exception:  # noqa: BLE001 - redact secrets from unexpected transport/database failures
            # Never print exception URLs, request bodies or the webhook token.
            logger.error("Discord worker iteration failed; retrying later")
        time.sleep(2)
