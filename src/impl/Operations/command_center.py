"""Private event status, incidents and audited judging recovery."""

from collections import Counter
from copy import deepcopy
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_sqlalchemy import db
from pydantic import BaseModel, Field
from sqlalchemy import func

from src.impl.Event.model import HackerAccepted, HackerParticipation, HackerRegistration
from src.impl.HackerGroup.model import HackerGroup
from src.impl.Meal.model import HackerMeal, Meal
from src.impl.Operations import judging
from src.impl.Operations import service as ops
from src.impl.Operations.model import EventIncident, OperationAudit, Presentation
from src.impl.Operations.realtime import broadcast_alerts
from src.utils.JWTBearer import JWTBearer

router = APIRouter(prefix="/operations", tags=["Event Operations"])


@router.get("/{event_id}/status")
def status(event_id: int, token=Depends(JWTBearer())):
    ops.require_organizer(token)
    _, row = ops.state(event_id)
    expected = (
        db.session.query(HackerRegistration)
        .join(
            HackerAccepted,
            (HackerAccepted.event_id == HackerRegistration.event_id)
            & (HackerAccepted.user_id == HackerRegistration.user_id),
        )
        .filter(
            HackerRegistration.event_id == event_id,
            HackerRegistration.confirmed_assistance.is_(True),
        )
        .all()
    )
    checked = {
        p.user_id
        for p in db.session.query(HackerParticipation).filter_by(event_id=event_id)
    }
    expected_ids = {r.user_id for r in expected}
    restrictions = Counter((r.food_restrictions or "").strip() for r in expected)
    restrictions.pop("", None)
    teams = dict(
        db.session.query(HackerGroup.id, HackerGroup.name).filter_by(event_id=event_id)
    )
    turns = judging.room_turns(event_id)
    meals = (
        db.session.query(Meal.id, Meal.name, func.count(HackerMeal.user_id))
        .outerjoin(HackerMeal, HackerMeal.meal_id == Meal.id)
        .filter(Meal.event_id == event_id)
        .group_by(Meal.id, Meal.name)
        .all()
    )
    incidents = (
        db.session.query(EventIncident)
        .filter_by(event_id=event_id)
        .order_by(EventIncident.id.desc())
        .limit(100)
        .all()
    )
    recent = (
        db.session.query(OperationAudit)
        .filter(
            OperationAudit.event_id == event_id, OperationAudit.outcome != "success"
        )
        .order_by(OperationAudit.id.desc())
        .limit(10)
        .all()
    )
    result = {
        "server_time": datetime.now(UTC),
        "version": row.version,
        "phase": ops.effective_phase(row.config),
        "attendance": {
            "expected": len(expected),
            "checked_in": len(checked),
            "pending": len(expected_ids - checked),
        },
        "dietary": [
            {"restriction": k, "count": v} for k, v in sorted(restrictions.items())
        ],
        "meals": [
            {"id": mid, "name": name, "served": count} for mid, name, count in meals
        ],
        "rooms": [
            {
                **room,
                "presentations": [
                    {
                        "id": p.id,
                        "team": teams.get(p.group_id, ""),
                        "state": p.state,
                        "started_at": p.started_at,
                    }
                    for p in turns
                    if p.room == room["id"] and p.state in {"presenting", "called"}
                ],
            }
            for room in row.config.get("rooms", [])
        ],
        "incidents": [i.to_dict() for i in incidents],
        "recent_rejections": [
            {"id": a.id, "action": a.action, "created_at": a.created_at} for a in recent
        ],
    }
    db.session.commit()
    return result


class IncidentInput(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    details: str = Field(default="", max_length=2000)
    operation_id: UUID


@router.post("/{event_id}/incidents")
def create_incident(event_id: int, body: IncidentInput, token=Depends(JWTBearer())):
    ops.require_organizer(token)
    ops.state(event_id, True)
    details = body.model_dump(mode="json")
    previous = (
        db.session.query(OperationAudit)
        .filter_by(event_id=event_id, operation_id=str(body.operation_id))
        .first()
    )
    if previous:
        if previous.action != "incident.create" or previous.details != details:
            raise HTTPException(
                409, "Operation identifier already used for a different request"
            )
        return previous.result
    incident = EventIncident(
        event_id=event_id,
        title=body.title,
        details=body.details,
        status="open",
        version=0,
    )
    db.session.add(incident)
    db.session.flush()
    log = ops.audit(
        event_id, token, "incident.create", details, operation_id=str(body.operation_id)
    )
    log.result = {"id": incident.id}
    db.session.commit()
    return log.result


class IncidentUpdate(BaseModel):
    version: int = Field(ge=0)
    status: Literal["open", "resolved"]


@router.patch("/{event_id}/incidents/{incident_id}")
def update_incident(
    event_id: int, incident_id: int, body: IncidentUpdate, token=Depends(JWTBearer())
):
    ops.require_organizer(token)
    ops.state(event_id, True)
    incident = (
        db.session.query(EventIncident)
        .filter_by(event_id=event_id, id=incident_id)
        .first()
    )
    if not incident:
        raise HTTPException(404, "Incident not found")
    if incident.version != body.version:
        raise HTTPException(409, "Incident changed; refresh first")
    incident.status = body.status
    incident.version += 1
    incident.resolved_at = datetime.now(UTC) if body.status == "resolved" else None
    ops.audit(event_id, token, "incident." + body.status, {"incident_id": incident_id})
    db.session.commit()
    return {"ok": True}


class RecoveryInput(BaseModel):
    version: int = Field(ge=0)
    action: Literal["absent", "requeue", "move"]
    room: str | None = None
    reason: str = Field(min_length=3, max_length=500)
    operation_id: UUID


@router.post("/{event_id}/presentations/{presentation_id}/recovery")
def recover(
    event_id: int, presentation_id: int, body: RecoveryInput, token=Depends(JWTBearer())
):
    ops.require_organizer(token)
    _, row = ops.state(event_id, True)
    p = (
        db.session.query(Presentation)
        .filter_by(event_id=event_id, id=presentation_id)
        .first()
    )
    if not p:
        raise HTTPException(404, "Presentation not found")
    details = {**body.model_dump(mode="json"), "presentation_id": presentation_id}
    previous = (
        db.session.query(OperationAudit)
        .filter_by(event_id=event_id, operation_id=str(body.operation_id))
        .first()
    )
    if previous:
        if previous.action != "judging.recovery" or previous.details != details:
            raise HTTPException(
                409, "Operation identifier already used for a different request"
            )
        return previous.result
    if p.version != body.version:
        raise HTTPException(409, "Presentation changed; refresh first")
    if p.state == "presenting":
        raise HTTPException(409, "Finish the current presentation before recovery")
    if body.action == "absent" and p.state not in {"waiting", "called", "postponed"}:
        raise HTTPException(409, "Only pending presentations can be marked absent")
    if body.action == "requeue" and p.state not in {"absent", "postponed", "called"}:
        raise HTTPException(
            409, "Only absent, postponed or called presentations can be requeued"
        )
    if body.action == "move":
        if p.state == "done":
            raise HTTPException(409, "Completed presentations cannot be moved")
        if body.room not in {r["id"] for r in row.config.get("rooms", [])}:
            raise HTTPException(422, "Unknown room")
    changes = []
    old_room = p.room
    if body.action == "absent":
        judging.transition(p, "absent", changes)
    else:
        if body.action == "move":
            p.room = body.room
        judging.transition(p, "waiting", changes)
        p.position = (
            max(
                (q.position for q in judging.room_turns(event_id) if q.room == p.room),
                default=0,
            )
            + 1
        )
        p.started_at = p.completed_at = p.scheduled_at = None
        p.duration_seconds = 300
        p.pinned = 0
    if ops.effective_phase(row.config) == "judging" and ops.challenges_released(
        row.config
    ):
        judging.refresh_queue(
            event_id, old_room, row.config, judging.room_turns(event_id), changes
        )
        judging.announce_called(row, changes)
    row.version += 1
    log = ops.audit(
        event_id,
        token,
        "judging.recovery",
        details,
        operation_id=str(body.operation_id),
    )
    log.result = {"ok": True, "transitions": changes, "previous_room": old_room}
    db.session.commit()
    broadcast_alerts(event_id)
    return log.result


class RoomInput(BaseModel):
    version: int = Field(ge=0)
    paused: bool
    reason: str = Field(min_length=3, max_length=500)


@router.post("/{event_id}/rooms/{room_id}/pause")
def pause_room(
    event_id: int, room_id: str, body: RoomInput, token=Depends(JWTBearer())
):
    ops.require_organizer(token)
    _, row = ops.state(event_id, True)
    if row.version != body.version:
        raise HTTPException(409, "Configuration changed; refresh before saving")
    config = deepcopy(row.config)
    room = next((r for r in config.get("rooms", []) if r["id"] == room_id), None)
    if room is None:
        raise HTTPException(404, "Room not found")
    room["paused"] = body.paused
    row.config = config
    row.version += 1
    changes = []
    if (
        not body.paused
        and ops.effective_phase(config) == "judging"
        and ops.challenges_released(config)
    ):
        judging.refresh_queue(
            event_id, room_id, config, judging.room_turns(event_id), changes
        )
        judging.announce_called(row, changes)
    ops.audit(
        event_id,
        token,
        "judging.room_pause",
        {"room": room_id, **body.model_dump(), "transitions": changes},
    )
    db.session.commit()
    broadcast_alerts(event_id)
    return {"ok": True}
