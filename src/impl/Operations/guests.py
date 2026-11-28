"""Event guests: name + email identities with a "Convidat" or "Empresa" ticket."""

import logging
import re
import unicodedata
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi_sqlalchemy import db
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, insert

from src.impl.Event.model import EventTicketDelivery
from src.impl.Hacker.model import Hacker
from src.impl.Operations.model import EventGuest
from src.impl.User.model import User
from src.impl.User.schema import UserCreate
from src.impl.UserConfig.model import UserConfig
from src.impl.Voucher.model import Voucher
from src.utils.access import require_management
from src.utils.JWTBearer import JWTBearer
from src.utils.security import get_password_hash

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/operations/{event_id}/guests", tags=["Event guests"])


def _email(value):
    return UserCreate.email_validation(value).lower() if value else value


class CreateGuest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=3, max_length=254)
    kind: Literal["convidat", "empresa"] = "convidat"

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        return _email(value)


class UpdateGuest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str | None = Field(default=None, min_length=2, max_length=150)
    email: str | None = Field(default=None, min_length=3, max_length=254)
    active: bool | None = None

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        return _email(value)


def _find_by_email(email, exclude_id=None):
    query = db.session.query(User).filter(func.lower(User.email) == email)
    if exclude_id is not None:
        query = query.filter(User.id != exclude_id)
    return query.first()


@router.get("")
def list_guests(
    event_id: int,
    kind: Literal["convidat", "empresa"] | None = None,
    token=Depends(JWTBearer()),
):
    require_management(token)
    query = (
        db.session.query(EventGuest, User)
        .join(User, User.id == EventGuest.user_id)
        .filter(EventGuest.event_id == event_id)
    )
    if kind:
        query = query.filter(EventGuest.kind == kind)
    rows = query.order_by(User.name, User.id).all()
    deliveries = {
        d.user_id: d.ticket_sent_at
        for d in db.session.query(EventTicketDelivery).filter_by(event_id=event_id)
    }
    badges = {
        v.hacker_id
        for v in db.session.query(Voucher).filter_by(event_id=event_id, revoked=False)
        if v.hacker_id
    }
    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "kind": entry.kind,
            "active": entry.active,
            "ticket_sent_at": deliveries.get(user.id),
            "has_badge": user.id in badges,
        }
        for entry, user in rows
    ]


@router.post("")
def create_guest(event_id: int, body: CreateGuest, token=Depends(JWTBearer())):
    from src.impl.Operations.service import audit, state

    require_management(token)
    state(event_id, lock=True)
    user = _find_by_email(body.email)
    if user is not None and (user.access_role != "guest" or user.is_deleted):
        raise HTTPException(
            409, "Email belongs to an existing account that is not a guest"
        )
    if user is None:
        config = UserConfig()
        db.session.add(config)
        db.session.flush()
        # Guests only hold a ticket: no password, no login, no participant profile.
        user = User(
            name=body.name,
            email=body.email,
            nickname=f"guest-{uuid4().hex}",
            access_role="guest",
            password="!",
            code=uuid4().hex,
            config_id=config.id,
            is_verified=False,
        )
        db.session.add(user)
        db.session.flush()
    else:
        # The same person can be invited to several editions; keep one identity.
        user.name = body.name
    entry = db.session.get(EventGuest, (event_id, user.id))
    if entry is not None and entry.active:
        raise HTTPException(409, "Guest already invited to this event")
    if entry is None:
        db.session.add(EventGuest(event_id=event_id, user_id=user.id, kind=body.kind))
    else:
        entry.active = True
        entry.kind = body.kind
    audit(
        event_id,
        token,
        "guest.create",
        {"name": user.name, "kind": body.kind},
        user.id,
    )
    db.session.commit()
    return {"id": user.id, "name": user.name, "email": user.email, "kind": body.kind}


@router.patch("/{user_id}")
def update_guest(
    event_id: int, user_id: int, body: UpdateGuest, token=Depends(JWTBearer())
):
    from src.impl.Operations.service import audit, state

    require_management(token)
    state(event_id, lock=True)
    entry = db.session.get(EventGuest, (event_id, user_id))
    user = db.session.get(User, user_id)
    if not entry or not user or user.access_role != "guest":
        raise HTTPException(404, "Guest not found")
    if body.active is not None:
        entry.active = body.active
    if body.name is not None:
        user.name = body.name
    if body.email is not None and body.email != (user.email or "").lower():
        if _find_by_email(body.email, exclude_id=user.id):
            raise HTTPException(409, "Email belongs to another account")
        user.email = body.email
        # A ticket mailed to the old address must be sent again.
        for delivery in db.session.query(EventTicketDelivery).filter_by(
            user_id=user.id
        ):
            delivery.ticket_sent_at = None
    audit(
        event_id,
        token,
        "guest.update",
        {"fields": sorted(body.model_fields_set)},
        user_id,
    )
    db.session.commit()
    return {"ok": True}


def _hacker_nickname(name):
    """A readable, unique nickname instead of the internal guest-<uuid> one."""
    ascii_name = (
        unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode()
    )
    base = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")[:40] or "hacker"
    nickname, n = base, 1
    while db.session.query(User.id).filter(User.nickname == nickname).first():
        n += 1
        nickname = f"{base}-{n}"
    return nickname


@router.post("/{user_id}/promote")
def promote_guest(event_id: int, user_id: int, token=Depends(JWTBearer())):
    """Turn a guest into a hacker account, keeping the same identity.

    The guest ticket is withdrawn everywhere and a password reset mail lets the
    person sign in and register to the event like any other participant.
    """
    from src.impl.Authentication.service import AuthenticationService
    from src.impl.Operations.service import audit, state

    require_management(token)
    state(event_id, lock=True)
    entry = db.session.get(EventGuest, (event_id, user_id))
    user = db.session.get(User, user_id, with_for_update=True)
    if not entry or not user or user.access_role != "guest":
        raise HTTPException(404, "Guest not found")
    if user.is_deleted:
        raise HTTPException(409, "Account is not available")
    if not user.email:
        raise HTTPException(409, "Guest has no email")
    email, name = user.email, user.name
    # Joined-table inheritance: add the hacker row, then switch the discriminator.
    db.session.execute(insert(Hacker.__table__).values(user_id=user.id))
    user.type = "hacker"
    user.access_role = "hacker"
    user.nickname = _hacker_nickname(user.name)
    # Unusable until the reset mail sets a real one ("!" is not a valid hash).
    user.password = get_password_hash(uuid4().hex)
    # Organizers typed this address; the reset mail still proves ownership.
    user.is_verified = True
    for guest in db.session.query(EventGuest).filter_by(user_id=user.id):
        guest.active = False
    audit(event_id, token, "guest.promote", {"name": name}, user.id)
    db.session.commit()
    # The cached User instance has the old polymorphic class; reload as Hacker.
    db.session.expunge_all()
    try:
        AuthenticationService().reset_password(email)
        password_mail = True
    except Exception:  # the promotion is already committed
        logger.exception("Password mail failed for promoted guest %s", user_id)
        password_mail = False
    return {"id": user_id, "email": email, "password_mail": password_mail}
