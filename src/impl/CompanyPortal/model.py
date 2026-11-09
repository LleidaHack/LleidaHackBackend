"""Private company judging identities, event grants and versioned evaluations."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.Base.BaseModel import BaseModel


class PortalAccount(BaseModel):
    __tablename__ = "company_portal_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), unique=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class PortalGrant(BaseModel):
    __tablename__ = "company_portal_grant"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("company_portal_account.id"))
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"))
    rooms: Mapped[list] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    winner_id: Mapped[int | None] = mapped_column(
        ForeignKey("hacker_group.id", ondelete="SET NULL")
    )
    version: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (UniqueConstraint("account_id", "event_id"),)


class PortalSession(BaseModel):
    __tablename__ = "company_portal_session"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("company_portal_account.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PortalInvitation(BaseModel):
    __tablename__ = "company_portal_invitation"
    id: Mapped[int] = mapped_column(primary_key=True)
    operation_id: Mapped[str] = mapped_column(String(36), unique=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("company_portal_account.id"))
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_state: Mapped[str] = mapped_column(String(30), default="pending")
    delivery_url: Mapped[str | None] = mapped_column(Text)
    mail_id: Mapped[int | None] = mapped_column(Integer)
    fingerprint: Mapped[str] = mapped_column(String(64))


class PortalNote(BaseModel):
    __tablename__ = "company_portal_note"
    id: Mapped[int] = mapped_column(primary_key=True)
    grant_id: Mapped[int] = mapped_column(ForeignKey("company_portal_grant.id"))
    group_id: Mapped[int] = mapped_column(
        ForeignKey("hacker_group.id", ondelete="CASCADE")
    )
    text: Mapped[str] = mapped_column(Text, default="")
    score: Mapped[int | None] = mapped_column(Integer)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("grant_id", "group_id"),)
