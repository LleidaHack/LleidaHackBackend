"""Badge-driven presentation transitions under the event transaction lock."""

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from fastapi_sqlalchemy import db

from src.impl.HackerGroup.model import HackerGroup, HackerGroupUser
from src.impl.Operations.model import Presentation


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
    turns = (
        db.session.query(Presentation)
        .filter_by(event_id=event_id)
        .order_by(Presentation.position, Presentation.id)
        .all()
    )
    own = [p for p in turns if p.group_id == group.id and p.room == room_id]
    if len(own) != 1:
        raise HTTPException(409, "Team has no unique presentation in this room")
    current = own[0]
    if current.state in {"done", "absent"}:
        raise HTTPException(409, "Team presentation is already closed")
    if current.state == "presenting":
        return {"team": group.name, "already_presenting": True}
    now = datetime.now(UTC)
    travel = timedelta(minutes=config.get("travel_minutes", 5))

    def available(p, for_start=True):
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

    if not available(current):
        raise HTTPException(409, "Team is busy in another room or still travelling")
    changes = []

    def transition(p, state):
        changes.append({"id": p.id, "before": p.state, "after": state})
        p.state = state
        p.version += 1

    for p in turns:
        if p.room != room_id or p.id == current.id:
            continue
        if p.state == "presenting":
            transition(p, "done")
            p.completed_at = now
        elif p.state == "called":
            transition(p, "waiting")
    transition(current, "presenting")
    current.started_at = now
    next_team = None
    # Refresh every room after a completion: MLH can call a newly freed team
    # while it walks over, but the start scan still enforces the travel buffer.
    room_order = [room] + [r for r in config.get("rooms", []) if r["id"] != room_id]
    for candidate_room in room_order:
        if candidate_room.get("paused"):
            continue
        called = next(
            (
                p
                for p in turns
                if p.room == candidate_room["id"] and p.state == "called"
            ),
            None,
        )
        if called is None:
            called = next(
                (
                    p
                    for p in turns
                    if p.room == candidate_room["id"]
                    and p.state == "waiting"
                    and available(p, for_start=False)
                ),
                None,
            )
            if called:
                transition(called, "called")
        if called and candidate_room["id"] == room_id:
            next_team = db.session.get(HackerGroup, called.group_id).name
    log.details = {
        **log.details,
        "room": room_id,
        "group_id": group.id,
        "transitions": changes,
    }
    return {"team": group.name, "next_team": next_team, "presentation_id": current.id}
