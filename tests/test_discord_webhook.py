from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import httpx
import pytest
from sqlalchemy.orm import Session

from src.impl.Operations.discord_messages import discord_message, webhook_url
from src.impl.Operations.discord_worker import deliver_one
from src.impl.Operations.model import DiscordDelivery


@pytest.fixture
def webhook(client, create_user, create_event, monkeypatch):
    organizer = create_user(role="organizer")
    event = create_event([])
    monkeypatch.setenv(
        "DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/123/test-token"
    )
    monkeypatch.setenv("DISCORD_WEBHOOK_EVENT_ID", str(event))
    base = f"/v1/operations/{event}"
    body = {
        "title": "Dinner",
        "message": "Come eat @everyone",
        "discord": True,
        "live": False,
        "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        "discord_card": {
            "color": "#ff7430",
            "url": "https://example.org/meal",
            "image_url": "https://example.org/image.png",
            "fields": [{"name": "Location", "value": "Hall"}],
        },
    }
    response = client.post(base + "/alerts", headers=organizer.headers, json=body)
    assert response.status_code == 200, response.text
    return event, organizer, base, body


def row_state(engine):
    with Session(engine) as session:
        row = session.query(DiscordDelivery).one()
        return row.state, row.attempts, row.message_id, row.error


def test_webhook_sends_embed_and_records_receipt_once(client, engine, webhook):
    event, organizer, base, _ = webhook
    post = Mock(return_value=httpx.Response(200, json={"id": "123456789"}))
    assert deliver_one(engine, event, post)
    assert row_state(engine) == ("sent", 1, "123456789", None)
    assert not deliver_one(engine, event, post)
    post.assert_called_once()
    kwargs = post.call_args.kwargs
    assert kwargs["params"] == {"wait": "true"}
    assert kwargs["follow_redirects"] is False
    assert kwargs["json"]["allowed_mentions"] == {"parse": []}
    embed = kwargs["json"]["embeds"][0]
    assert embed["title"] == "Dinner"
    assert embed["color"] == 0xFF7430
    assert embed["image"]["url"] == "https://example.org/image.png"
    assert embed["fields"][0]["name"] == "Location"
    result = client.get(base + "/discord-deliveries", headers=organizer.headers)
    assert result.json()["mode"] == "webhook"
    assert "test-token" not in result.text


def test_rate_limit_schedules_retry_and_preserves_payload(engine, webhook):
    event, *_ = webhook
    post = Mock(return_value=httpx.Response(429, json={"retry_after": 120}))
    assert deliver_one(engine, event, post)
    assert not deliver_one(engine, event, post)
    assert row_state(engine)[:2] == ("pending", 1)
    post.assert_called_once()
    with Session(engine) as session:
        row = session.query(DiscordDelivery).one()
        assert row.lease_until > datetime.now(UTC) + timedelta(seconds=100)
        row.lease_until = datetime.now(UTC) - timedelta(seconds=1)
        session.commit()
    post.return_value = httpx.Response(200, json={"id": "42"})
    assert deliver_one(engine, event, post)
    assert row_state(engine)[:3] == ("sent", 2, "42")


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_permanent_errors_fail_without_leaking_response(engine, webhook, status):
    event, *_ = webhook
    post = Mock(return_value=httpx.Response(status, text="test-token private response"))
    deliver_one(engine, event, post)
    state, _, _, error = row_state(engine)
    assert state == "failed" and "test-token" not in error
    assert not deliver_one(engine, event, post)


def test_ambiguous_timeout_does_not_blindly_duplicate(engine, webhook):
    event, *_ = webhook
    post = Mock(side_effect=httpx.ReadTimeout("secret webhook URL"))
    deliver_one(engine, event, post)
    assert row_state(engine)[0] == "failed"
    assert "secret" not in row_state(engine)[3]
    assert not deliver_one(engine, event, post)


def test_cancelled_expired_and_other_event_messages_are_not_sent(engine, webhook):
    event, *_ = webhook
    post = Mock()
    assert not deliver_one(engine, event + 1, post)
    with Session(engine) as session:
        row = session.query(DiscordDelivery).one()
        row.state = "cancelled"
        session.commit()
    assert not deliver_one(engine, event, post)
    with Session(engine) as session:
        row = session.query(DiscordDelivery).one()
        row.state = "pending"
        row.payload = {
            **row.payload,
            "expires_at": (datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
        }
        session.commit()
    deliver_one(engine, event, post)
    assert row_state(engine)[0] == "expired"
    post.assert_not_called()


def test_retry_budget_and_transient_failures(engine, webhook):
    event, *_ = webhook
    post = Mock(return_value=httpx.Response(503))
    deliver_one(engine, event, post)
    assert row_state(engine)[:2] == ("pending", 1)
    with Session(engine) as session:
        row = session.query(DiscordDelivery).one()
        row.lease_until = None
        row.attempts = 4
        session.commit()
    deliver_one(engine, event, post)
    assert row_state(engine)[:2] == ("failed", 5)


def test_card_validation_and_permissions(client, create_user, webhook):
    _, organizer, base, body = webhook
    hacker = create_user()
    assert (
        client.post(base + "/alerts", headers=hacker.headers, json=body).status_code
        == 403
    )
    for card in (
        {"image_url": "http://example.org/image.png"},
        {"color": "bad"},
        {"fields": [{"name": "x", "value": "y"}] * 6},
        {"allowed_mentions": {"parse": ["everyone"]}},
    ):
        response = client.post(
            base + "/alerts",
            headers=organizer.headers,
            json={**body, "discord_card": card},
        )
        assert response.status_code == 422


def test_webhook_destination_is_not_arbitrary(monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_EVENT_ID", "1")
    for url in (
        "http://discord.com/api/webhooks/1/token",
        "https://example.com/api/webhooks/1/token",
        "https://discord.com.evil.test/api/webhooks/1/token",
        "https://discord.com/api/webhooks/1/token?redirect=evil",
    ):
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", url)
        assert webhook_url(1) is None


def test_plain_message_disables_mentions():
    result = discord_message(
        {"title": "Hello", "message": "@everyone", "discord_card": {"enabled": False}}
    )
    assert result == {
        "content": "**Hello**\n@everyone",
        "allowed_mentions": {"parse": []},
    }


def test_worker_lock_prevents_parallel_senders(engine, webhook):
    from sqlalchemy import text

    event, *_ = webhook
    post = Mock()
    with engine.begin() as connection:
        connection.execute(
            text("SELECT pg_advisory_xact_lock(76430, :event)"), {"event": event}
        )
        assert not deliver_one(engine, event, post)
    post.assert_not_called()


def test_webhook_configuration_disables_duplicate_bot_consumption(
    client, webhook, monkeypatch
):
    event, _, base, _ = webhook
    monkeypatch.setenv("DISCORD_BOT_SHARED_SECRET", "test-bot-secret")
    monkeypatch.setenv("DISCORD_BOT_EVENT_ID", str(event))
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123")
    response = client.post(
        base + "/discord/claim", headers={"X-Discord-Bot-Key": "test-bot-secret"}
    )
    assert response.status_code == 403
