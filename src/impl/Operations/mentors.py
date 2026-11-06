"""Small event mentor roster; mentors receive meals via a physical badge only."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi_sqlalchemy import db
from pydantic import BaseModel, ConfigDict, Field

from src.impl.Mentor.model import Mentor
from src.impl.Operations.model import EventMentor
from src.impl.User.model import User
from src.impl.UserConfig.model import UserConfig
from src.impl.Voucher.model import Voucher
from src.utils.access import require_management
from src.utils.JWTBearer import JWTBearer

router = APIRouter(prefix="/operations/{event_id}/mentors", tags=["Event mentors"])


class CreateMentor(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=150)
    user_id: int | None = None


class BadgeInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    code: str = Field(min_length=1, max_length=100)
    replace: bool = False


class MentorStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    active: bool


def roster(event_id):
    rows = (
        db.session.query(EventMentor, User)
        .join(User, User.id == EventMentor.user_id)
        .filter(EventMentor.event_id == event_id)
        .order_by(User.name, User.id)
        .all()
    )
    badges = {
        v.hacker_id: v
        for v in db.session.query(Voucher).filter_by(event_id=event_id, revoked=False)
        if v.hacker_id
    }
    return [
        {
            "id": u.id,
            "name": u.name,
            "active": entry.active,
            "has_badge": u.id in badges,
        }
        for entry, u in rows
    ]


@router.get("")
def list_mentors(event_id: int, token=Depends(JWTBearer())):
    require_management(token)
    return roster(event_id)


@router.get("/candidates")
def existing_mentors(event_id: int, token=Depends(JWTBearer())):
    require_management(token)
    linked = [
        entry.user_id
        for entry in db.session.query(EventMentor).filter_by(event_id=event_id)
    ]
    return [
        {"id": user.id, "name": user.name}
        for user in db.session.query(User)
        .filter(User.access_role == "mentor", User.is_deleted.is_(False))
        .order_by(User.name)
        if user.id not in linked
    ]


@router.post("")
def create_mentor(event_id: int, body: CreateMentor, token=Depends(JWTBearer())):
    from src.impl.Operations.service import audit, state

    require_management(token)
    state(event_id, lock=True)
    if body.user_id:
        user = db.session.get(User, body.user_id)
        if not user or user.access_role != "mentor" or user.is_deleted:
            raise HTTPException(422, "Select an existing user with the mentor role")
    else:
        config = UserConfig()
        db.session.add(config)
        db.session.flush()
        # No login credentials or ticket are issued for a roster-only mentor.
        user = Mentor(
            name=body.name,
            nickname=f"mentor-{uuid4().hex}",
            access_role="mentor",
            password="!",
            code=uuid4().hex,
            config_id=config.id,
            is_verified=False,
        )
        db.session.add(user)
        db.session.flush()
    if db.session.get(EventMentor, (event_id, user.id)):
        raise HTTPException(409, "Mentor already registered for this event")
    db.session.add(EventMentor(event_id=event_id, user_id=user.id))
    audit(event_id, token, "mentor.create", {"name": user.name}, user.id)
    db.session.commit()
    return {"id": user.id, "name": user.name}


@router.patch("/{user_id}")
def change_status(
    event_id: int, user_id: int, body: MentorStatus, token=Depends(JWTBearer())
):
    from src.impl.Operations.service import audit, state

    require_management(token)
    state(event_id, lock=True)
    entry = db.session.get(EventMentor, (event_id, user_id))
    if not entry:
        raise HTTPException(404, "Mentor not found")
    entry.active = body.active
    audit(event_id, token, "mentor.status", {"active": body.active}, user_id)
    db.session.commit()
    return {"ok": True}


@router.put("/{user_id}/badge")
def bind_badge(
    event_id: int, user_id: int, body: BadgeInput, token=Depends(JWTBearer())
):
    from src.impl.Operations.service import audit, organizer, state

    if not organizer(token):
        raise HTTPException(403, "Organizer permission required")
    if body.replace:
        require_management(token)
    state(event_id, lock=True)
    entry = db.session.get(EventMentor, (event_id, user_id))
    user = db.session.get(User, user_id)
    if not entry or not entry.active or not user or user.access_role != "mentor":
        raise HTTPException(404, "Active mentor not found")
    badge = (
        db.session.query(Voucher).filter_by(event_id=event_id, code=body.code).first()
    )
    if not badge or badge.revoked:
        raise HTTPException(404, "Free badge not found")
    if badge.hacker_id == user_id:
        return {"ok": True, "participant": user.name}
    if badge.hacker_id is not None:
        raise HTTPException(409, "Badge already assigned")
    previous = (
        db.session.query(Voucher)
        .filter_by(event_id=event_id, hacker_id=user_id)
        .first()
    )
    if previous and not body.replace:
        raise HTTPException(
            409, "Participant already has a badge; ask an admin to replace it"
        )
    if previous:
        previous.hacker_id = None
        previous.revoked = True
        db.session.flush()
    badge.hacker_id = user_id
    badge.assigned_at = datetime.now(UTC).replace(tzinfo=None)
    audit(
        event_id,
        token,
        "mentor.badge.replace" if previous else "mentor.badge.assign",
        {
            "voucher_id": badge.id,
            "previous_voucher_id": previous.id if previous else None,
        },
        user_id,
    )
    db.session.commit()
    return {"ok": True, "participant": user.name}
