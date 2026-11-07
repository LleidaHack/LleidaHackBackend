"""Shared Discord message formatting and server-only webhook configuration."""

import os
import re


def webhook_url(event_id):
    url = os.getenv("DISCORD_WEBHOOK_URL", "")
    if os.getenv("DISCORD_WEBHOOK_EVENT_ID") != str(event_id):
        return None
    if not re.fullmatch(
        r"https://discord\.com/api(?:/v10)?/webhooks/[0-9]+/[A-Za-z0-9_-]+", url
    ):
        return None
    return url


def discord_message(payload):
    card = payload.get("discord_card") or {}
    if not card.get("enabled", True):
        return {
            "content": f"**{payload['title']}**\n{payload['message']}"[:2000],
            "allowed_mentions": {"parse": []},
        }
    color = card.get("color") or {
        "info": "#ff7430",
        "warning": "#e6a23c",
        "danger": "#d64545",
    }.get(payload.get("level"), "#ff7430")
    embed = {
        "title": payload["title"],
        "description": payload["message"],
        "color": int(color.lstrip("#"), 16),
        "footer": {"text": card.get("footer") or "HackEPS · LleidaHack"},
    }
    if payload.get("created_at"):
        embed["timestamp"] = payload["created_at"]
    for field in ("image", "thumbnail"):
        if card.get(f"{field}_url"):
            embed[field] = {"url": card[f"{field}_url"]}
    if card.get("url"):
        embed["url"] = card["url"]
    if card.get("fields"):
        embed["fields"] = card["fields"]
    return {"embeds": [embed], "allowed_mentions": {"parse": []}}
