from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.utils.Base.BaseModel import BaseModel

if TYPE_CHECKING:
    from src.impl.Hacker.model import Hacker


class Voucher(BaseModel):
    """Physical accreditation handed out at check-in.

    Vouchers are generated in bulk before the event (one QR per printed badge)
    and bound to a hacker when their ticket is scanned at the door. During the
    event meals and activities are scanned against the voucher, not the ticket.
    """

    __tablename__ = "event_voucher"
    __table_args__ = (
        UniqueConstraint("event_id", "hacker_id", name="uq_event_voucher_hacker"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("event.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    hacker_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("hacker.user_id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    hacker: Mapped[Hacker | None] = relationship("Hacker", foreign_keys=[hacker_id])
