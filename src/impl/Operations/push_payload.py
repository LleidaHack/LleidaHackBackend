"""Bound serialized Web Push payloads, including Unicode and JSON escaping."""

import json

MAX_PAYLOAD_BYTES = 3000
FIELDS = (
    "id",
    "title",
    "message",
    "level",
    "category",
    "expires_at",
    "created_at",
    "event_id",
    "live",
)


def compact_push_payload(alert):
    payload = {key: alert[key] for key in FIELDS if key in alert}
    message = payload.get("message", "")
    if len(message) > 1000:
        message = message[:999] + "…"
    payload["message"] = message
    if len(json.dumps(payload).encode("utf-8")) <= MAX_PAYLOAD_BYTES:
        return payload
    low, high = 0, len(message)
    while low < high:
        middle = (low + high + 1) // 2
        payload["message"] = message[:middle] + "…"
        if len(json.dumps(payload).encode("utf-8")) <= MAX_PAYLOAD_BYTES:
            low = middle
        else:
            high = middle - 1
    payload["message"] = message[:low] + "…"
    if len(json.dumps(payload).encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise ValueError("Push metadata exceeds the payload budget")
    return payload
