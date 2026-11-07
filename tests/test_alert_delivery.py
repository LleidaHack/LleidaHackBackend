from datetime import UTC, datetime, timedelta


def alert_body(**overrides):
    return {
        "title": "Dinner",
        "message": "Dinner is ready @everyone",
        "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        **overrides,
    }


def test_discord_outbox_scope_leases_ack_and_live_visibility(
    client, create_user, create_event, monkeypatch
):
    admin = create_user(role="admin")
    staff = create_user(role="lleidahacker")
    event = create_event([])
    base = f"/v1/operations/{event}"
    response = client.post(
        base + "/alerts",
        headers=admin.headers,
        json=alert_body(live=False, discord=True),
    )
    assert response.status_code == 200, response.text
    assert client.get(base + "/public").json()["alerts"] == []
    status = client.get(base + "/discord-deliveries", headers=admin.headers).json()
    assert status["configured"] is False
    assert status["deliveries"][0]["state"] == "pending"
    assert (
        client.get(base + "/discord-deliveries", headers=staff.headers).status_code
        == 403
    )
    assert client.post(base + "/discord/claim").status_code == 403
    monkeypatch.setenv("DISCORD_BOT_SHARED_SECRET", "test-bot-key-only")
    monkeypatch.setenv("DISCORD_BOT_EVENT_ID", str(event))
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
    headers = {"X-Discord-Bot-Key": "test-bot-key-only"}
    assert (
        client.post(
            f"/v1/operations/{event + 1}/discord/claim", headers=headers
        ).status_code
        == 403
    )
    items = client.post(base + "/discord/claim", headers=headers).json()
    assert len(items) == 1
    delivery = items[0]
    assert delivery["message"]["allowed_mentions"] == {"parse": []}
    assert client.post(base + "/discord/claim", headers=headers).json() == []
    ack = base + f"/discord/{delivery['id']}/ack"
    assert (
        client.post(
            ack, headers=headers, json={"lease_token": "wrong", "message_id": "123"}
        ).status_code
        == 409
    )
    payload = {"lease_token": delivery["lease_token"], "message_id": "123"}
    assert client.post(ack, headers=headers, json=payload).status_code == 200
    assert client.post(ack, headers=headers, json=payload).status_code == 200
    status = client.get(base + "/discord-deliveries", headers=admin.headers).json()
    assert status["deliveries"][0]["state"] == "sent"
    assert "lease_token" not in status["deliveries"][0]


def test_alert_cancellation_and_destinations(
    client, create_user, create_event, monkeypatch
):
    admin = create_user(role="admin")
    event = create_event([])
    base = f"/v1/operations/{event}"
    monkeypatch.setenv("DISCORD_BOT_SHARED_SECRET", "test-bot-key-only")
    monkeypatch.setenv("DISCORD_BOT_EVENT_ID", str(event))
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
    headers = {"X-Discord-Bot-Key": "test-bot-key-only"}
    assert (
        client.post(
            base + "/alerts", headers=admin.headers, json=alert_body(live=False)
        ).status_code
        == 422
    )
    alert = client.post(
        base + "/alerts", headers=admin.headers, json=alert_body(discord=True)
    ).json()
    delivery = client.post(base + "/discord/claim", headers=headers).json()[0]
    assert (
        client.delete(
            base + f"/alerts/{alert['id']}", headers=admin.headers
        ).status_code
        == 200
    )
    assert (
        client.post(
            base + f"/discord/{delivery['id']}/ack",
            headers=headers,
            json={"lease_token": delivery["lease_token"], "message_id": "123"},
        ).status_code
        == 409
    )
    assert client.get(base + "/public").json()["alerts"] == []


def test_live_websocket_receives_alert_and_removal(client, create_user, create_event):
    admin = create_user(role="admin")
    event = create_event([])
    base = f"/v1/operations/{event}"
    with client.websocket_connect(base + "/ws") as websocket:
        assert websocket.receive_json() == {"type": "alerts", "alerts": []}
        response = client.post(
            base + "/alerts", headers=admin.headers, json=alert_body()
        )
        assert response.status_code == 200, response.text

        def next_alerts():
            for _ in range(5):
                message = websocket.receive_json()
                if message["type"] == "alerts":
                    return message["alerts"]
            raise AssertionError("No alert broadcast received")

        alerts = next_alerts()
        assert alerts[0]["title"] == "Dinner"
        client.delete(base + f"/alerts/{alerts[0]['id']}", headers=admin.headers)
        assert next_alerts() == []


def test_discord_delivery_retry_and_expiry(
    client, create_user, create_event, engine, monkeypatch
):
    from sqlalchemy import text

    admin = create_user(role="admin")
    event = create_event([])
    base = f"/v1/operations/{event}"
    monkeypatch.setenv("DISCORD_BOT_SHARED_SECRET", "test-bot-key-only")
    monkeypatch.setenv("DISCORD_BOT_EVENT_ID", str(event))
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
    headers = {"X-Discord-Bot-Key": "test-bot-key-only"}
    client.post(base + "/alerts", headers=admin.headers, json=alert_body(discord=True))
    delivery = client.post(base + "/discord/claim", headers=headers).json()[0]
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE event_discord_delivery SET lease_until = now() - interval '1 second' WHERE id=:id"
            ),
            {"id": delivery["id"]},
        )
    retry = client.post(base + "/discord/claim", headers=headers).json()[0]
    assert retry["lease_token"] != delivery["lease_token"]
    assert (
        client.post(
            base + f"/discord/{delivery['id']}/ack",
            headers=headers,
            json={"lease_token": delivery["lease_token"], "message_id": "123"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            base + f"/discord/{retry['id']}/ack",
            headers=headers,
            json={
                "lease_token": retry["lease_token"],
                "error": "Temporary Discord outage",
            },
        ).status_code
        == 200
    )
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE event_discord_delivery SET attempts=5 WHERE id=:id"),
            {"id": delivery["id"]},
        )
    assert client.post(base + "/discord/claim", headers=headers).json() == []
    status = client.get(base + "/discord-deliveries", headers=admin.headers).json()
    assert status["deliveries"][0]["state"] == "failed"


def test_push_payload_is_compact(
    client, create_user, create_event, monkeypatch, engine
):
    from sqlalchemy.orm import Session

    from src.impl.Operations.model import PushDelivery

    admin = create_user(role="admin")
    event = create_event([])
    base = f"/v1/operations/{event}"
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-only")
    subscribed = client.post(
        base + "/subscribe",
        json={
            "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint",
            "keys": {"p256dh": "key", "auth": "auth"},
        },
    )
    assert subscribed.status_code == 200, subscribed.text
    response = client.post(
        base + "/alerts",
        headers=admin.headers,
        json=alert_body(
            message="x" * 2000,
            push=True,
            discord_card={"enabled": True, "footer": "y" * 200},
        ),
    )
    assert response.status_code == 200, response.text
    with Session(engine) as session:
        payload = session.query(PushDelivery).one().payload
    assert "discord_card" not in payload
    assert len(payload["message"]) == 1000 and payload["message"].endswith("…")
    assert payload["event_id"] == event and payload["id"] == response.json()["id"]
