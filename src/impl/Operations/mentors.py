"""Event mentor roster, invitation contacts and physical meal badges."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi_sqlalchemy import db
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func

from src.impl.Mentor.model import Mentor
from src.impl.Operations.model import EventMentor
from src.impl.User.model import User
from src.impl.User.schema import UserCreate
from src.impl.UserConfig.model import UserConfig
from src.impl.Voucher.model import Voucher
from src.utils.access import require_management
from src.utils.JWTBearer import JWTBearer

router = APIRouter(prefix="/operations/{event_id}/mentors", tags=["Event mentors"])


class CreateMentor(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=150)
    user_id: int | None = None
    email: str | None = Field(default=None, max_length=254)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        return UserCreate.email_validation(value).lower() if value else None


class BadgeInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    code: str = Field(min_length=1, max_length=100)
    replace: bool = False


class MentorStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    active: bool | None = None
    email: str | None = Field(default=None, max_length=254)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        return UserCreate.email_validation(value).lower() if value else None


def roster(event_id, include_email=False):
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
            **(
                {
                    "email": entry.invitation_email
                    if entry.invitation_email is not None
                    else u.email
                }
                if include_email
                else {}
            ),
            "active": entry.active,
            "has_badge": u.id in badges,
        }
        for entry, u in rows
    ]


@router.get("")
def list_mentors(event_id: int, token=Depends(JWTBearer())):
    require_management(token)
    return roster(event_id, include_email=True)


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
        existing = (
            db.session.query(User).filter(func.lower(User.email) == body.email).first()
            if body.email
            else None
        )
        if existing:
            if existing.access_role != "mentor" or existing.is_deleted:
                raise HTTPException(
                    409, "Email belongs to an existing account; select a mentor account"
                )
            user = existing
        else:
            user = None
    if not body.user_id and user is None:
        config = UserConfig()
        db.session.add(config)
        db.session.flush()
        # Roster-only identities can receive tickets, but have no login credentials.
        user = Mentor(
            name=body.name,
            email=body.email,
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
    db.session.add(
        EventMentor(event_id=event_id, user_id=user.id, invitation_email=body.email)
    )
    audit(event_id, token, "mentor.create", {"name": user.name}, user.id)
    db.session.commit()
    return {"id": user.id, "name": user.name, "email": user.email}


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
    if body.active is not None:
        entry.active = body.active
    if "email" in body.model_fields_set:
        from src.impl.Event.model import EventTicketDelivery

        user = db.session.get(User, user_id)
        previous = (
            entry.invitation_email if entry.invitation_email is not None else user.email
        )
        entry.invitation_email = body.email or ""
        delivery = db.session.get(EventTicketDelivery, (event_id, user_id))
        if delivery and (previous or "") != entry.invitation_email:
            delivery.ticket_sent_at = None
    audit(
        event_id,
        token,
        "mentor.update",
        {"fields": sorted(body.model_fields_set)},
        user_id,
    )
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
