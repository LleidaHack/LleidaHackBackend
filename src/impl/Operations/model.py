"""Persistent event operations; all financial and scan writes use event row locks."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.Base.BaseModel import BaseModel


class EventOperations(BaseModel):
    __tablename__ = "event_operations"
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, default=0)
    config: Mapped[dict] = mapped_column(JSON, default=dict)


class OperationAudit(BaseModel):
    __tablename__ = "operation_audit"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), index=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("my_user.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("my_user.id"))
    action: Mapped[str] = mapped_column(String(60))
    outcome: Mapped[str] = mapped_column(String(30))
    operation_id: Mapped[str] = mapped_column(String(100))
    device: Mapped[str] = mapped_column(String(100), default="")
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (UniqueConstraint("event_id", "operation_id"),)


class ScanRecord(BaseModel):
    __tablename__ = "operation_scan"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("my_user.id"))
    kind: Mapped[str] = mapped_column(String(30))
    target: Mapped[str] = mapped_column(String(100))
    round: Mapped[int] = mapped_column(Integer, default=1)
    audit_id: Mapped[int | None] = mapped_column(ForeignKey("operation_audit.id"))
    voided: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    __table_args__ = (
        Index(
            "uq_active_operation_scan",
            "event_id",
            "user_id",
            "kind",
            "target",
            "round",
            unique=True,
            postgresql_where=text("NOT voided"),
        ),
    )


class CoinMovement(BaseModel):
    __tablename__ = "coin_movement"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("my_user.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    balance_before: Mapped[int] = mapped_column(Integer)
    balance_after: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(500))
    audit_id: Mapped[int] = mapped_column(ForeignKey("operation_audit.id"))
    reversal_of: Mapped[int | None] = mapped_column(
        ForeignKey("coin_movement.id"), unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Presentation(BaseModel):
    duration_seconds: Mapped[int] = mapped_column(
        Integer, default=300, server_default="300"
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __tablename__ = "event_presentation"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), index=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("hacker_group.id", ondelete="CASCADE")
    )
    room: Mapped[str] = mapped_column(String(80))
    track: Mapped[str] = mapped_column(String(80))
    position: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    state: Mapped[str] = mapped_column(String(30), default="waiting")
    pinned: Mapped[int] = mapped_column(Integer, default=0)
    version: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (UniqueConstraint("event_id", "group_id", "track"),)


class PushSubscription(BaseModel):
    __tablename__ = "event_push_subscription"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), index=True)
    endpoint: Mapped[str] = mapped_column(String, unique=True)
    subscription: Mapped[dict] = mapped_column(JSON)


class PushDelivery(BaseModel):
    __tablename__ = "event_push_delivery"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"))
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("event_push_subscription.id")
    )
    alert_id: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict] = mapped_column(JSON)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    state: Mapped[str] = mapped_column(String(30), default="pending")
    __table_args__ = (UniqueConstraint("subscription_id", "alert_id"),)


class AccessRoleAudit(BaseModel):
    __tablename__ = "access_role_audit"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("my_user.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("my_user.id"), index=True)
    previous_role: Mapped[str] = mapped_column(String(30))
    new_role: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DiscordDelivery(BaseModel):
    __tablename__ = "event_discord_delivery"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), index=True)
    alert_id: Mapped[str] = mapped_column(String(100), unique=True)
    payload: Mapped[dict] = mapped_column(JSON)
    state: Mapped[str] = mapped_column(String(30), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    lease_token: Mapped[str | None] = mapped_column(String(100))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    message_id: Mapped[str | None] = mapped_column(String(100))
    error: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DevpostProject(BaseModel):
    description: Mapped[str] = mapped_column(
        String(10000), default="", server_default=""
    )
    repository_url: Mapped[str] = mapped_column(
        String(500), default="", server_default=""
    )
    demo_url: Mapped[str] = mapped_column(String(500), default="", server_default="")
    __tablename__ = "event_devpost_project"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), index=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("hacker_group.id", ondelete="CASCADE")
    )
    url: Mapped[str] = mapped_column(String(500))
    title: Mapped[str] = mapped_column(String(150))
    challenge: Mapped[str] = mapped_column(String(80))
    mlh: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (
        UniqueConstraint("event_id", "url"),
        UniqueConstraint("event_id", "group_id"),
    )


class ChallengeVote(BaseModel):
    __tablename__ = "event_challenge_vote"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), index=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("hacker_group.id", ondelete="CASCADE")
    )
    challenge: Mapped[str] = mapped_column(String(80))
    version: Mapped[int] = mapped_column(Integer, default=1)
    __table_args__ = (UniqueConstraint("event_id", "group_id"),)


class NicknameRequest(BaseModel):
    __tablename__ = "nickname_request"
    __table_args__ = (
        Index(
            "uq_nickname_pending",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("my_user.id"), index=True)
    previous: Mapped[str] = mapped_column(String)
    proposed: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("my_user.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EventMentor(BaseModel):
    __tablename__ = "event_mentor"
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("my_user.id"), primary_key=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
