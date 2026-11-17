"""Judging room for teams entering the Josep Maria Ribó prize."""

from fastapi import HTTPException
from fastapi_sqlalchemy import db

from src.impl.Operations.model import Presentation

ROOM_ID = "josep-maria-ribo"


def ensure_room(state):
    rooms = state.config.get("rooms", [])
    if not any(room["id"] == ROOM_ID for room in rooms):
        state.config = {
            **state.config,
            "rooms": [
                *rooms,
                {"id": ROOM_ID, "title": "Josep Maria Ribó", "paused": False},
            ],
        }
        state.version += 1


def sync_choice(state, group_id, participating):
    if participating:
        ensure_room(state)
    turns = (
        db.session.query(Presentation)
        .filter_by(event_id=state.event_id, group_id=group_id)
        .all()
    )
    prize_turn = next((turn for turn in turns if turn.track == ROOM_ID), None)
    if participating and turns and not prize_turn:
        db.session.add(
            Presentation(
                event_id=state.event_id, group_id=group_id, room=ROOM_ID, track=ROOM_ID
            )
        )
        state.version += 1
    elif not participating and prize_turn:
        if prize_turn.state not in {"waiting", "postponed"}:
            raise HTTPException(409, "Prize presentation has already started or closed")
        db.session.delete(prize_turn)
        state.version += 1
