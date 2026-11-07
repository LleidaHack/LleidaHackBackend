"""Nickname changes only become public after an audited management decision."""

import unicodedata
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi_sqlalchemy import db
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError

from src.impl.Operations.model import NicknameRequest
from src.impl.User.model import User
from src.utils.access import require_management
from src.utils.JWTBearer import JWTBearer

router = APIRouter(prefix="/nicknames", tags=["Nickname moderation"])


class Proposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nickname: str = Field(min_length=2, max_length=40)

    @field_validator("nickname")
    @classmethod
    def validate_name(cls, value):
        value = unicodedata.normalize("NFKC", value).strip()
        if not 2 <= len(value) <= 40 or not all(
            c.isalnum() or c in " _-." for c in value
        ):
            raise ValueError(
                "Use 2–40 letters, numbers, spaces, underscores, dots or hyphens"
            )
        return value


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["approve", "reject"]


def lock():
    db.session.execute(text("SELECT pg_advisory_xact_lock(71465032)"))


def available(name, user_id):
    if (
        db.session.query(User)
        .filter(func.lower(User.nickname) == name.lower(), User.id != user_id)
        .first()
    ):
        raise HTTPException(409, "Nickname already exists")


def commit():
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise HTTPException(
            409, "Nickname already exists or request is pending"
        ) from None


@router.get("/me")
def mine(token=Depends(JWTBearer())):
    user = db.session.get(User, token.user_id) if token.user_id else None
    if user is None:
        raise HTTPException(404, "No user profile for this token")
    return {
        "nickname": user.nickname,
        "requests": [
            r.to_dict()
            for r in db.session.query(NicknameRequest)
            .filter_by(user_id=token.user_id)
            .order_by(NicknameRequest.id.desc())
            .limit(20)
        ],
    }


@router.post("/me")
def propose(body: Proposal, token=Depends(JWTBearer())):
    if not token.user_id:
        raise HTTPException(404, "No user profile for this token")
    lock()
    user = db.session.get(User, token.user_id, populate_existing=True)
    if (
        db.session.query(NicknameRequest)
        .filter_by(user_id=user.id, status="pending")
        .first()
    ):
        raise HTTPException(409, "A nickname request is already pending")
    if body.nickname == user.nickname:
        raise HTTPException(422, "Choose a different nickname")
    available(body.nickname, user.id)
    item = NicknameRequest(
        user_id=user.id, previous=user.nickname, proposed=body.nickname
    )
    db.session.add(item)
    commit()
    return item.to_dict()


@router.get("/requests")
def requests(token=Depends(JWTBearer())):
    require_management(token)
    return [
        r.to_dict()
        for r in db.session.query(NicknameRequest)
        .order_by(
            (NicknameRequest.status == "pending").desc(), NicknameRequest.id.desc()
        )
        .limit(200)
    ]


@router.post("/requests/{request_id}")
def decide(request_id: int, body: Decision, token=Depends(JWTBearer())):
    require_management(token)
    lock()
    item = db.session.get(NicknameRequest, request_id, populate_existing=True)
    if not item:
        raise HTTPException(404, "Request not found")
    if item.status != "pending":
        raise HTTPException(409, "Request already resolved")
    user = db.session.get(User, item.user_id, populate_existing=True)
    if body.action == "approve":
        if user.nickname != item.previous:
            raise HTTPException(409, "Nickname changed since this request")
        available(item.proposed, user.id)
        user.nickname = item.proposed
    item.status = "approved" if body.action == "approve" else "rejected"
    item.actor_id = token.user_id
    item.resolved_at = datetime.now(UTC)
    commit()
    return item.to_dict()


@router.post("/users/{user_id}")
def correct(user_id: int, body: Proposal, token=Depends(JWTBearer())):
    require_management(token)
    lock()
    user = db.session.get(User, user_id, populate_existing=True)
    if not user or user.is_deleted:
        raise HTTPException(404, "User not found")
    available(body.nickname, user.id)
    now = datetime.now(UTC)
    for pending in db.session.query(NicknameRequest).filter_by(
        user_id=user.id, status="pending"
    ):
        pending.status, pending.actor_id, pending.resolved_at = (
            "superseded",
            token.user_id,
            now,
        )
    item = NicknameRequest(
        user_id=user.id,
        previous=user.nickname,
        proposed=body.nickname,
        status="corrected",
        actor_id=token.user_id,
        resolved_at=now,
    )
    user.nickname = body.nickname
    db.session.add(item)
    commit()
    return item.to_dict()
