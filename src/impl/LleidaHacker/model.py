from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.impl.User.model import User
from src.utils.user_type import UserType

if TYPE_CHECKING:
    from src.impl.Event.model import Event
    from src.impl.LleidaHackerGroup.model import LleidaHackerGroup


class LleidaHacker(User):
    __tablename__ = 'lleida_hacker'
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('my_user.id'), primary_key=True
    )
    role: Mapped[str] = mapped_column(String)
    nif: Mapped[str] = mapped_column(String, unique=True)
    student: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    linkedin: Mapped[str] = mapped_column(String, default='')
    github: Mapped[str | None] = mapped_column(String)
    accepted: Mapped[bool] = mapped_column(Boolean, default=True)
    # rejected: Mapped[bool] = mapped_column(Boolean, default=False)
    groups: Mapped[list[LleidaHackerGroup]] = relationship(
        'LleidaHackerGroup', secondary='lleida_hacker_group_user'
    )
    events: Mapped[list[Event]] = relationship(
        'Event', secondary='lleida_hacker_event_participation'
    )

    __mapper_args__ = {
        'polymorphic_identity': UserType.LLEIDAHACKER.value,
    }
