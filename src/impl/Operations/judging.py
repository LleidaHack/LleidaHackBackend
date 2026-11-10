"""Scanned room admission and company-controlled presentation timing."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from fastapi_sqlalchemy import db

from src.impl.HackerGroup.model import HackerGroup, HackerGroupUser
from src.impl.Operations.model import Presentation


def room_turns(event_id):
    return (
        db.session.query(Presentation)
        .filter_by(event_id=event_id)
        .order_by(Presentation.position, Presentation.id)
        .all()
    )


def transition(p, state, changes):
    changes.append({"id": p.id, "before": p.state, "after": state})
    p.state = state
    p.version += 1


def available(p, turns, config, for_start=False):
    now = datetime.now(UTC)
    travel = timedelta(minutes=config.get("travel_minutes", 5))
    return not any(
        q.group_id == p.group_id
        and q.room != p.room
        and (
            q.state in {"called", "presenting"}
            or (
                for_start
                and q.completed_at is not None
                and q.completed_at + travel > now
            )
        )
        for q in turns
    )


def refresh_queue(event_id, room_id, config, turns, changes):
    """Keep one called team per unpaused room, without admitting it automatically."""
    next_team = None
    rooms = sorted(config.get("rooms", []), key=lambda r: r["id"] != room_id)
    for room in rooms:
        if room.get("paused"):
            continue
        called = next(
            (p for p in turns if p.room == room["id"] and p.state == "called"), None
        )
        if called is None:
            called = next(
                (
                    p
                    for p in turns
                    if p.room == room["id"]
                    and p.state == "waiting"
                    and available(p, turns, config)
                ),
                None,
            )
            if called:
                transition(called, "called", changes)
        if called and room["id"] == room_id:
            next_team = db.session.get(HackerGroup, called.group_id).name
    return next_team


def announce_called(row, changes):
    """Publish new queue calls on Live in the same transaction as the transition."""
    calls = [change for change in changes if change["after"] == "called"]
    if not calls:
        return
    config = deepcopy(row.config)
    now = datetime.now(UTC)
    alerts = [
        a
        for a in config.get("alerts", [])
        if datetime.fromisoformat(a["expires_at"]) > now
    ]
    labels = {r["id"]: r.get("title", r["id"]) for r in config.get("rooms", [])}
    for change in calls:
        turn = db.session.get(Presentation, change["id"])
        team = db.session.get(HackerGroup, turn.group_id)
        alerts.append(
            {
                "id": str(uuid4()),
                "event_id": row.event_id,
                "title": "Prepareu-vos per presentar",
                "message": f"{team.name}: aneu a la sala d’espera de {labels.get(turn.room, turn.room)}.",
                "level": "info",
                "category": "general",
                "live": True,
                "push": False,
                "discord": False,
                "created_at": now.isoformat(),
                "expires_at": (now + timedelta(minutes=10)).isoformat(),
            }
        )
    config["alerts"] = alerts
    row.config = config


def start_presentation(event_id, user_id, room_id, config, log):
    from src.impl.Operations.service import challenges_released, effective_phase

    if not challenges_released(config) or effective_phase(config) != "judging":
        raise HTTPException(409, "Judging is not open")
    room = next((r for r in config.get("rooms", []) if r["id"] == room_id), None)
    if not room:
        raise HTTPException(422, "Unknown room")
    if room.get("paused"):
        raise HTTPException(409, "Room is paused")
    groups = (
        db.session.query(HackerGroup)
        .join(HackerGroupUser, HackerGroupUser.group_id == HackerGroup.id)
        .filter(HackerGroup.event_id == event_id, HackerGroupUser.hacker_id == user_id)
        .all()
    )
    if len(groups) != 1:
        raise HTTPException(409, "Participant must belong to exactly one event team")
    group = groups[0]
    turns = room_turns(event_id)
    own = [p for p in turns if p.group_id == group.id and p.room == room_id]
    if len(own) != 1:
        raise HTTPException(409, "Team has no unique presentation in this room")
    current = own[0]
    if current.state in {"done", "absent"}:
        raise HTTPException(409, "Team presentation is already closed")
    if current.state == "presenting":
        return {
            "team": group.name,
            "already_presenting": True,
            "presentation_id": current.id,
            "timer_started": current.started_at is not None,
        }
    if any(p.room == room_id and p.state == "presenting" for p in turns):
        raise HTTPException(
            409, "Finish the current presentation in the company portal first"
        )
    if not available(current, turns, config, for_start=True):
        raise HTTPException(409, "Team is busy in another room or still travelling")
    changes = []
    transition(current, "presenting", changes)
    current.started_at = None
    current.completed_at = None
    current.duration_seconds = 300
    next_team = refresh_queue(event_id, room_id, config, turns, changes)
    log.details = {
        **log.details,
        "room": room_id,
        "group_id": group.id,
        "transitions": changes,
    }
    return {
        "team": group.name,
        "next_team": next_team,
        "presentation_id": current.id,
        "timer_started": False,
    }
