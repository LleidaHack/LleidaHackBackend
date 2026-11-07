from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi_sqlalchemy import db
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text

from src.impl.Operations.model import AccessRoleAudit
from src.impl.User.model import User
from src.utils.access import require_superadmin
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(prefix="/access", tags=["Access Roles"])


class RoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["superadmin", "admin", "lleidahacker", "hacker", "mentor"]
    reason: str = Field(min_length=3, max_length=500)


def assign_role(user_id, body, token, event_id=None):
    require_superadmin(token)
    db.session.execute(text("SELECT pg_advisory_xact_lock(71465031)"))
    if token.user_id:
        actor = db.session.get(User, token.user_id, populate_existing=True)
        if not actor or actor.access_role != "superadmin":
            raise HTTPException(403, "Superadmin permission required")
    user = db.session.get(User, user_id, populate_existing=True)
    if not user or user.is_deleted:
        raise HTTPException(404, "User not found")
    if user_id == token.user_id and body.role != "superadmin":
        raise HTTPException(409, "You cannot remove your own superadmin access")
    if user.access_role == "superadmin" and body.role != "superadmin":
        others = [
            u
            for u in db.session.query(User).filter(
                User.access_role == "superadmin",
                User.id != user_id,
                User.is_deleted.is_(False),
            )
            if BaseToken.is_available(u)
        ]
        if not others:
            raise HTTPException(409, "The last superadmin cannot be removed")
    previous = user.access_role
    user.access_role = body.role
    db.session.add(
        AccessRoleAudit(
            actor_id=token.user_id or None,
            user_id=user_id,
            previous_role=previous,
            new_role=body.role,
            reason=body.reason,
        )
    )
    if event_id is not None:
        from src.impl.Operations.service import audit

        audit(
            event_id,
            token,
            "staff.role",
            {"before": previous, "after": body.role, "reason": body.reason},
            user_id,
        )
    db.session.commit()
    return {"ok": True, "user_id": user_id, "access_role": body.role}


@router.patch("/users/{user_id}/role")
def change_role(
    user_id: int, body: RoleUpdate, token: BaseToken = Depends(JWTBearer())
):
    return assign_role(user_id, body, token)


@router.get("/users/{user_id}/history")
def role_history(user_id: int, token: BaseToken = Depends(JWTBearer())):
    require_superadmin(token)
    return [
        entry.to_dict()
        for entry in db.session.query(AccessRoleAudit)
        .filter_by(user_id=user_id)
        .order_by(AccessRoleAudit.id.desc())
        .limit(100)
    ]
