"""A narrowly scoped pull/ack contract for the future official Discord bot."""

import os
from datetime import UTC, datetime, timedelta
from secrets import compare_digest
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi_sqlalchemy import db
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import or_

from src.impl.Operations.discord_messages import discord_message, webhook_url
from src.impl.Operations.model import DiscordDelivery
from src.utils.access import require_management
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(prefix="/operations", tags=["Event Operations"])


def bot_configured(event_id):
    return bool(
        os.getenv("DISCORD_BOT_SHARED_SECRET")
        and os.getenv("DISCORD_CHANNEL_ID")
        and os.getenv("DISCORD_BOT_EVENT_ID") == str(event_id)
    )


def authorize_bot(event_id: int, x_discord_bot_key: str = Header(default="")):
    secret = os.getenv("DISCORD_BOT_SHARED_SECRET", "")
    if (
        webhook_url(event_id)
        or not bot_configured(event_id)
        or not compare_digest(x_discord_bot_key.encode(), secret.encode())
    ):
        raise HTTPException(403, "Discord bot credentials required")


@router.get("/{event_id}/discord-deliveries")
def deliveries(event_id: int, token: BaseToken = Depends(JWTBearer())):
    require_management(token)
    rows = (
        db.session.query(DiscordDelivery)
        .filter_by(event_id=event_id)
        .order_by(DiscordDelivery.id.desc())
        .limit(100)
    )
    return {
        "configured": bool(webhook_url(event_id)) or bot_configured(event_id),
        "mode": "webhook"
        if webhook_url(event_id)
        else "bot"
        if bot_configured(event_id)
        else None,
        "deliveries": [
            {
                key: getattr(row, key)
                for key in (
                    "id",
                    "alert_id",
                    "state",
                    "attempts",
                    "message_id",
                    "error",
                    "created_at",
                )
            }
            for row in rows
        ],
    }


@router.post("/{event_id}/discord/claim", dependencies=[Depends(authorize_bot)])
def claim(event_id: int):
    now = datetime.now(UTC)
    rows = (
        db.session.query(DiscordDelivery)
        .filter(
            DiscordDelivery.event_id == event_id,
            or_(
                DiscordDelivery.state == "pending",
                (DiscordDelivery.state == "leased")
                & (DiscordDelivery.lease_until <= now),
            ),
        )
        .order_by(DiscordDelivery.id)
        .with_for_update(skip_locked=True)
        .limit(20)
        .all()
    )
    result = []
    for row in rows:
        if datetime.fromisoformat(row.payload["expires_at"]) <= now:
            row.state = "expired"
            continue
        if row.attempts >= 5:
            row.state = "failed"
            continue
        row.state = "leased"
        row.attempts += 1
        row.lease_token = str(uuid4())
        row.lease_until = now + timedelta(minutes=2)
        # Discord bot must preserve allowed_mentions; organizer text cannot ping everyone.
        result.append(
            {
                "id": row.id,
                "alert_id": row.alert_id,
                "lease_token": row.lease_token,
                "lease_until": row.lease_until,
                "channel_id": os.environ["DISCORD_CHANNEL_ID"],
                "message": discord_message(row.payload),
            }
        )
    db.session.commit()
    return result


class DeliveryAck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lease_token: str
    message_id: str | None = Field(default=None, pattern=r"^[0-9]{1,30}$")
    error: str | None = Field(default=None, max_length=500)


@router.post(
    "/{event_id}/discord/{delivery_id}/ack", dependencies=[Depends(authorize_bot)]
)
def acknowledge(event_id: int, delivery_id: int, body: DeliveryAck):
    row = (
        db.session.query(DiscordDelivery)
        .filter_by(id=delivery_id, event_id=event_id)
        .with_for_update()
        .first()
    )
    if not row or row.lease_token != body.lease_token:
        raise HTTPException(409, "Delivery lease changed")
    if row.state == "sent" and row.message_id == body.message_id:
        return {"ok": True}
    if row.state != "leased" or row.lease_until <= datetime.now(UTC):
        raise HTTPException(409, "Delivery lease expired or cancelled")
    if bool(body.message_id) == bool(body.error):
        raise HTTPException(422, "Provide either a Discord message ID or an error")
    row.state = (
        "sent" if body.message_id else ("failed" if row.attempts >= 5 else "pending")
    )
    row.message_id = body.message_id
    row.error = body.error
    db.session.commit()
    return {"ok": True}
