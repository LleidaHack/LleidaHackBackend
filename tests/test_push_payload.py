import json

import pytest

from src.impl.Operations.push_payload import MAX_PAYLOAD_BYTES, compact_push_payload


@pytest.fixture(autouse=True)
def database():
    pass


@pytest.fixture(autouse=True)
def clean_database():
    pass


@pytest.mark.parametrize("character", ["🚜", "é", "漢", "\\", '"', "x"])
def test_serialized_unicode_payload_fits(character):
    alert = {
        "id": "test",
        "title": "🚜" * 150,
        "message": character * 2000,
        "event_id": 1,
        "expires_at": "2026-11-07T20:00:00Z",
        "discord_card": {"description": "x" * 10000},
        "live": True,
    }
    payload = compact_push_payload(alert)
    assert len(json.dumps(payload).encode()) <= MAX_PAYLOAD_BYTES
    assert "discord_card" not in payload
    assert payload["message"].endswith("…")
    assert payload["title"] == alert["title"]
    assert compact_push_payload(payload) == payload
