"""Company-only judging access. Public Live snapshots never include evaluations."""

import hashlib
import json
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_sqlalchemy import db
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.impl.Company.model import Company
from src.impl.CompanyPortal.model import (
    PortalAccount,
    PortalGrant,
    PortalInvitation,
    PortalNote,
    PortalSession,
)
from src.impl.Event.model import Event
from src.impl.HackerGroup.model import HackerGroup
from src.impl.Operations.model import (
    DevpostProject,
    EventOperations,
    OperationAudit,
    Presentation,
)
from src.impl.Operations.service import audit, state
from src.utils.access import require_management
from src.utils.JWTBearer import JWTBearer
from src.utils.security import get_password_hash, validate_password, verify_password

router = APIRouter(prefix="/company-portal", tags=["Company portal"])
bearer = HTTPBearer(auto_error=False)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def now():
    return datetime.now(UTC)


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InviteInput(Input):
    company_id: int = Field(gt=0)
    email: str = Field(
        min_length=3, max_length=254, pattern=r"^[^\s@,]+@[^\s@,]+\.[^\s@,]+$"
    )
    rooms: list[str] = Field(min_length=1, max_length=30)
    operation_id: UUID

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().lower()


class LoginInput(Input):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=256)


class SetupInput(Input):
    token: str = Field(min_length=32, max_length=128)
    password: str = Field(max_length=256)

    @field_validator("password")
    @classmethod
    def check_password(cls, value):
        return validate_password(value)


class NoteInput(Input):
    version: int = Field(ge=0)
    text: str = Field(default="", max_length=10000)
    score: int | None = Field(default=None, ge=0, le=10)
    favorite: bool = False


class WinnerInput(Input):
    version: int = Field(ge=0)
    group_id: int | None = None


def account(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    session = (
        db.session.get(PortalSession, digest(credentials.credentials))
        if credentials
        else None
    )
    user = db.session.get(PortalAccount, session.account_id) if session else None
    if not session or session.expires_at <= now() or not user or not user.active:
        raise HTTPException(401, "Company session expired")
    return user


def grant_for(event_id, user, lock=False):
    query = db.session.query(PortalGrant).filter_by(
        event_id=event_id, account_id=user.id, active=True
    )
    grant = (query.with_for_update() if lock else query).first()
    if not grant:
        raise HTTPException(403, "Company has no access to this event")
    return grant


def authorized_groups(grant):
    return (
        db.session.query(Presentation.group_id)
        .filter(
            Presentation.event_id == grant.event_id, Presentation.room.in_(grant.rooms)
        )
        .distinct()
    )


def ensure_project(grant, group_id):
    if not authorized_groups(grant).filter(Presentation.group_id == group_id).first():
        raise HTTPException(404, "Project not found in assigned rooms")


def session_for(user):
    token = secrets.token_urlsafe(32)
    db.session.add(
        PortalSession(
            token_hash=digest(token),
            account_id=user.id,
            expires_at=now() + timedelta(days=7),
        )
    )
    db.session.commit()
    return {
        "access_token": token,
        "company": db.session.get(Company, user.company_id).name,
    }


@router.post("/login")
def login(body: LoginInput):
    user = (
        db.session.query(PortalAccount)
        .filter_by(email=body.email.strip().lower())
        .with_for_update()
        .first()
    )
    if (
        not user
        or not user.active
        or not user.password_hash
        or not verify_password(body.password, user.password_hash)
    ):
        raise HTTPException(401, "Invalid company credentials")
    return session_for(user)


@router.post("/setup")
def setup(body: SetupInput):
    invitation = (
        db.session.query(PortalInvitation)
        .filter_by(token_hash=digest(body.token))
        .first()
    )
    if not invitation or invitation.consumed or invitation.expires_at <= now():
        raise HTTPException(400, "Invitation expired or already used")
    user = (
        db.session.query(PortalAccount)
        .filter_by(id=invitation.account_id)
        .with_for_update()
        .one()
    )
    invitation = (
        db.session.query(PortalInvitation)
        .filter_by(id=invitation.id)
        .populate_existing()
        .with_for_update()
        .one()
    )
    if invitation.consumed or invitation.expires_at <= now():
        raise HTTPException(400, "Invitation expired or already used")
    if not user.active:
        raise HTTPException(403, "Company account is inactive")
    user.password_hash = get_password_hash(body.password)
    invitation.consumed = True
    invitation.delivery_url = None
    db.session.query(PortalSession).filter_by(account_id=user.id).delete()
    return session_for(user)


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer), user=Depends(account)
):
    db.session.query(PortalSession).filter_by(
        token_hash=digest(credentials.credentials), account_id=user.id
    ).delete()
    db.session.commit()
    return {"success": True}


@router.get("/events")
def events(user=Depends(account)):
    return [
        {"id": event.id, "name": event.name}
        for event in db.session.query(Event)
        .join(PortalGrant, PortalGrant.event_id == Event.id)
        .filter(PortalGrant.account_id == user.id, PortalGrant.active.is_(True))
    ]


@router.get("/events/{event_id}")
def snapshot(event_id: int, user=Depends(account)):
    grant = grant_for(event_id, user)
    operations = db.session.get(EventOperations, event_id)
    config = operations.config if operations else {}
    room_labels = {
        r["id"]: r.get("title", r["id"])
        for r in config.get("rooms", [])
        if r["id"] in grant.rooms
    }
    challenge_labels = {
        c["id"]: c.get("title", c["id"]) for c in config.get("challenges", [])
    }
    groups = (
        db.session.query(HackerGroup)
        .filter(HackerGroup.id.in_(authorized_groups(grant)))
        .all()
    )
    projects = {
        p.group_id: p
        for p in db.session.query(DevpostProject).filter_by(event_id=event_id)
    }
    notes = {
        n.group_id: n for n in db.session.query(PortalNote).filter_by(grant_id=grant.id)
    }
    turns = (
        db.session.query(Presentation)
        .filter(Presentation.event_id == event_id, Presentation.room.in_(grant.rooms))
        .order_by(Presentation.position, Presentation.id)
        .all()
    )
    return {
        "company": db.session.get(Company, user.company_id).name,
        "server_time": now(),
        "duration_seconds": 300,
        "version": grant.version,
        "winner_id": grant.winner_id,
        "finalized_at": grant.finalized_at,
        "rooms": grant.rooms,
        "room_labels": room_labels,
        "projects": [
            {
                "id": g.id,
                "team": g.name,
                "title": projects[g.id].title if g.id in projects else g.name,
                "description": (projects[g.id].description if g.id in projects else "")
                or g.description
                or "",
                "repository_url": projects[g.id].repository_url
                if g.id in projects
                else None,
                "demo_url": projects[g.id].demo_url if g.id in projects else None,
                "members": [m.name for m in g.members],
                "url": projects[g.id].url if g.id in projects else None,
                "challenge": challenge_labels.get(
                    projects[g.id].challenge, projects[g.id].challenge
                )
                if g.id in projects
                else None,
                "note": note_view(notes.get(g.id)),
            }
            for g in groups
        ],
        "presentations": [
            {
                "id": p.id,
                "group_id": p.group_id,
                "room": p.room,
                "state": p.state,
                "version": p.version,
                "duration_seconds": p.duration_seconds,
                "started_at": p.started_at,
                "scheduled_at": p.scheduled_at,
            }
            for p in turns
        ],
    }


def note_view(note):
    return {
        "text": note.text if note else "",
        "score": note.score if note else None,
        "favorite": note.favorite if note else False,
        "version": note.version if note else 0,
        "updated_at": note.updated_at.isoformat() if note else None,
    }


@router.put("/events/{event_id}/notes/{group_id}")
def save_note(event_id: int, group_id: int, body: NoteInput, user=Depends(account)):
    grant = grant_for(event_id, user, lock=True)
    if grant.finalized_at:
        raise HTTPException(
            409, "Company evaluation is finalized; contact the organization"
        )
    ensure_project(grant, group_id)
    note = (
        db.session.query(PortalNote)
        .filter_by(grant_id=grant.id, group_id=group_id)
        .first()
    )
    if (note.version if note else 0) != body.version:
        raise HTTPException(
            409,
            {"message": "Notes changed on another device", "current": note_view(note)},
        )
    if not note:
        note = PortalNote(grant_id=grant.id, group_id=group_id)
        db.session.add(note)
    note.text, note.score, note.favorite = body.text, body.score, body.favorite
    note.version = body.version + 1
    note.updated_at = now()
    grant.version += 1
    db.session.commit()
    return note_view(note)


@router.put("/events/{event_id}/winner")
def winner(event_id: int, body: WinnerInput, user=Depends(account)):
    grant = grant_for(event_id, user, lock=True)
    if grant.finalized_at:
        raise HTTPException(
            409, "Company evaluation is finalized; contact the organization"
        )
    if grant.version != body.version:
        raise HTTPException(409, "Company selection changed; refresh first")
    if body.group_id is not None:
        ensure_project(grant, body.group_id)
    grant.winner_id = body.group_id
    grant.version += 1
    db.session.commit()
    return {"version": grant.version, "winner_id": grant.winner_id}


@router.get("/manage/{event_id}")
def manage(event_id: int, token=Depends(JWTBearer())):
    require_management(token)
    rows = (
        db.session.query(PortalGrant, PortalAccount, Company)
        .join(PortalAccount, PortalGrant.account_id == PortalAccount.id)
        .join(Company, PortalAccount.company_id == Company.id)
        .filter(PortalGrant.event_id == event_id)
        .all()
    )
    result = []
    for grant, user, company in rows:
        invite = (
            db.session.query(PortalInvitation)
            .filter_by(account_id=user.id, event_id=event_id)
            .order_by(PortalInvitation.id.desc())
            .first()
        )
        result.append(
            {
                "company_id": company.id,
                "company": company.name,
                "email": user.email,
                "rooms": grant.rooms,
                "active": grant.active,
                "setup_complete": bool(user.password_hash),
                "version": grant.version,
                "winner_id": grant.winner_id,
                "finalized_at": grant.finalized_at,
                "delivery_state": invite.delivery_state if invite else None,
            }
        )
    return result


@router.post("/manage/{event_id}/invite")
def invite(event_id: int, body: InviteInput, token=Depends(JWTBearer())):
    require_management(token)
    _, config = state(event_id, lock=True)
    company = (
        db.session.query(Company)
        .filter_by(id=body.company_id)
        .with_for_update()
        .first()
    )
    if not company:
        raise HTTPException(404, "Company not found")
    valid_rooms = {room["id"] for room in config.config.get("rooms", [])}
    if not set(body.rooms) <= valid_rooms:
        raise HTTPException(422, "Select configured presentation rooms")
    fingerprint = digest(json.dumps(body.model_dump(mode="json"), sort_keys=True))
    previous = (
        db.session.query(PortalInvitation)
        .filter_by(operation_id=str(body.operation_id))
        .first()
    )
    if previous:
        if previous.fingerprint != fingerprint or previous.event_id != event_id:
            raise HTTPException(409, "Invitation operation was already used")
        return {"id": previous.id, "delivery_state": previous.delivery_state}
    user = (
        db.session.query(PortalAccount)
        .filter_by(company_id=company.id)
        .with_for_update()
        .first()
    )
    email_owner = db.session.query(PortalAccount).filter_by(email=body.email).first()
    if email_owner and email_owner != user:
        raise HTTPException(409, "Email already belongs to another company")
    if not user:
        user = PortalAccount(company_id=company.id, email=body.email)
        db.session.add(user)
        db.session.flush()
    elif user.email != body.email:
        raise HTTPException(409, "Use the existing company account email")
    grant = (
        db.session.query(PortalGrant)
        .filter_by(account_id=user.id, event_id=event_id)
        .with_for_update()
        .first()
    )
    if not grant:
        grant = PortalGrant(account_id=user.id, event_id=event_id)
        db.session.add(grant)
    if grant.rooms != sorted(set(body.rooms)) and grant.finalized_at:
        raise HTTPException(409, "Reopen the company evaluation before changing rooms")
    if grant.rooms != sorted(set(body.rooms)):
        grant.winner_id = None
        grant.version = (grant.version or 0) + 1
    grant.rooms, grant.active = sorted(set(body.rooms)), True
    # A new setup/reset invitation invalidates earlier unused links for this account.
    db.session.query(PortalInvitation).filter_by(
        account_id=user.id, consumed=False
    ).update({"consumed": True, "delivery_url": None}, synchronize_session=False)
    raw = secrets.token_urlsafe(32)
    origin = os.getenv("COMPANY_PORTAL_ORIGIN", "https://live.hackeps.dev").rstrip("/")
    invitation = PortalInvitation(
        operation_id=str(body.operation_id),
        account_id=user.id,
        event_id=event_id,
        token_hash=digest(raw),
        expires_at=now() + timedelta(hours=48),
        delivery_url=f"{origin}/companies#invite={raw}",
        fingerprint=fingerprint,
    )
    db.session.add(invitation)
    audit(
        event_id,
        token,
        "company.invite",
        {"company_id": company.id, "rooms": grant.rooms},
    )
    db.session.commit()
    return {"id": invitation.id, "delivery_state": invitation.delivery_state}


@router.delete("/manage/{event_id}/{company_id}")
def revoke(event_id: int, company_id: int, token=Depends(JWTBearer())):
    require_management(token)
    state(event_id, lock=True)
    user = (
        db.session.query(PortalAccount)
        .filter_by(company_id=company_id)
        .with_for_update()
        .first()
    )
    grant = (
        db.session.query(PortalGrant)
        .filter_by(event_id=event_id, account_id=user.id)
        .with_for_update()
        .first()
        if user
        else None
    )
    if not grant:
        raise HTTPException(404, "Company access not found")
    grant.active = False
    db.session.query(PortalInvitation).filter_by(
        account_id=user.id, event_id=event_id, consumed=False
    ).update({"consumed": True, "delivery_url": None}, synchronize_session=False)
    audit(event_id, token, "company.revoke", {"company_id": company_id})
    db.session.commit()
    return {"success": True}


class PresentationAction(Input):
    action: Literal["start", "extend", "finish"]
    version: int = Field(ge=0)
    operation_id: UUID


@router.post("/events/{event_id}/presentations/{presentation_id}/action")
def presentation_action(
    event_id: int, presentation_id: int, body: PresentationAction, user=Depends(account)
):
    from src.impl.Operations import judging
    from src.impl.Operations.realtime import broadcast_alerts
    from src.impl.Operations.service import challenges_released, effective_phase

    # Share the event lock with QR scans and organizer edits before locking grants.
    _, row = state(event_id, lock=True)
    grant = grant_for(event_id, user, lock=True)
    p = (
        db.session.query(Presentation)
        .filter_by(event_id=event_id, id=presentation_id)
        .first()
    )
    if not p or p.room not in grant.rooms:
        raise HTTPException(404, "Presentation not found in assigned rooms")
    fingerprint = digest(
        json.dumps(
            {
                **body.model_dump(mode="json"),
                "presentation_id": presentation_id,
                "account_id": user.id,
            },
            sort_keys=True,
        )
    )
    operation_id = "company-presentation:" + str(body.operation_id)
    previous = (
        db.session.query(OperationAudit)
        .filter_by(event_id=event_id, operation_id=operation_id)
        .first()
    )
    if previous:
        if previous.details.get("fingerprint") != fingerprint:
            raise HTTPException(409, "Presentation operation was already used")
        return previous.result
    if p.version != body.version:
        raise HTTPException(409, "Presentation changed; refresh first")
    if p.state != "presenting":
        raise HTTPException(
            409, "Scan the team into the room before controlling its presentation"
        )
    room = next((r for r in row.config.get("rooms", []) if r["id"] == p.room), None)
    if not room:
        raise HTTPException(409, "Presentation room is no longer configured")
    if body.action != "finish" and (
        room.get("paused")
        or not challenges_released(row.config)
        or effective_phase(row.config) != "judging"
    ):
        raise HTTPException(409, "Judging is not open or room is paused")
    changes = []
    next_team = None
    if body.action == "start":
        if p.started_at is not None:
            raise HTTPException(409, "Presentation timer is already running")
        p.started_at = now()
        p.duration_seconds = 300
        p.version += 1
    elif body.action == "extend":
        if p.started_at is None:
            raise HTTPException(409, "Start the presentation timer first")
        if p.duration_seconds >= 3600:
            raise HTTPException(422, "Presentation duration cannot exceed one hour")
        p.duration_seconds += 60
        p.version += 1
    else:
        judging.transition(p, "done", changes)
        p.completed_at = now()
        next_team = judging.refresh_queue(
            event_id, p.room, row.config, judging.room_turns(event_id), changes
        )
        judging.announce_called(row, changes)
    row.version += 1
    result = {
        "id": p.id,
        "state": p.state,
        "version": p.version,
        "started_at": p.started_at.isoformat() if p.started_at else None,
        "duration_seconds": p.duration_seconds,
        "next_team": next_team,
    }
    db.session.add(
        OperationAudit(
            event_id=event_id,
            actor_id=None,
            action="company.presentation." + body.action,
            outcome="success",
            operation_id=operation_id,
            details={
                "fingerprint": fingerprint,
                "company_id": user.company_id,
                "presentation_id": p.id,
                "transitions": changes,
            },
            result=result,
        )
    )
    db.session.commit()
    if body.action == "finish":
        broadcast_alerts(event_id)
    return result


class FinalizeInput(Input):
    version: int = Field(ge=0)
    group_id: int = Field(gt=0)
    operation_id: UUID


@router.post("/events/{event_id}/finalize")
def finalize(event_id: int, body: FinalizeInput, user=Depends(account)):
    state(event_id, lock=True)
    grant = grant_for(event_id, user, lock=True)
    details = {**body.model_dump(mode="json"), "company_id": user.company_id}
    operation_id = "company-finalize:" + str(body.operation_id)
    previous = (
        db.session.query(OperationAudit)
        .filter_by(event_id=event_id, operation_id=operation_id)
        .first()
    )
    if previous:
        if previous.details != details:
            raise HTTPException(409, "Company finalization operation was already used")
        return previous.result
    if grant.finalized_at or grant.version != body.version:
        raise HTTPException(409, "Company selection changed; refresh first")
    ensure_project(grant, body.group_id)
    if grant.winner_id != body.group_id:
        raise HTTPException(409, "Select the winner before confirming the decision")
    if (
        db.session.query(Presentation)
        .filter(
            Presentation.event_id == event_id,
            Presentation.room.in_(grant.rooms),
            Presentation.state.notin_(["done", "absent"]),
        )
        .first()
    ):
        raise HTTPException(409, "Finish all presentations before closing evaluations")
    grant.finalized_at = now()
    grant.version += 1
    result = {
        "version": grant.version,
        "winner_id": grant.winner_id,
        "finalized_at": grant.finalized_at.isoformat(),
    }
    db.session.add(
        OperationAudit(
            event_id=event_id,
            actor_id=None,
            action="company.finalize",
            outcome="success",
            operation_id=operation_id,
            details=details,
            result=result,
        )
    )
    db.session.commit()
    return result


class ReopenInput(Input):
    version: int = Field(ge=0)
    reason: str = Field(min_length=3, max_length=500)


@router.post("/manage/{event_id}/{company_id}/reopen")
def reopen(
    event_id: int, company_id: int, body: ReopenInput, token=Depends(JWTBearer())
):
    require_management(token)
    state(event_id, lock=True)
    user = db.session.query(PortalAccount).filter_by(company_id=company_id).first()
    grant = (
        db.session.query(PortalGrant)
        .filter_by(event_id=event_id, account_id=user.id)
        .with_for_update()
        .first()
        if user
        else None
    )
    if not grant:
        raise HTTPException(404, "Company access not found")
    if grant.version != body.version or not grant.finalized_at:
        raise HTTPException(409, "Company selection changed; refresh first")
    grant.finalized_at = None
    grant.version += 1
    audit(
        event_id,
        token,
        "company.reopen",
        {"company_id": company_id, "reason": body.reason},
    )
    db.session.commit()
    return {"ok": True}
