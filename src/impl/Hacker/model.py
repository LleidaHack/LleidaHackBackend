from __future__ import annotations

from typing import List, TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.impl.User.model import User
from src.utils.UserType import UserType

if TYPE_CHECKING:
    from src.impl.HackerGroup.model import HackerGroup
    from src.impl.Event.model import Event


class Hacker(User):
    __tablename__ = "hacker"
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("my_user.id"), primary_key=True
    )
    # banned: bool = mapped_column(Integer, default=0)
    banned: Mapped[bool] = mapped_column(Boolean, default=False)
    github: Mapped[str] = mapped_column(String, default="")
    linkedin: Mapped[str] = mapped_column(String, default="")
    cv: Mapped[str] = mapped_column(String, default="")
    studies: Mapped[str] = mapped_column(String, default="")
    study_center: Mapped[str] = mapped_column(String, default="")
    location: Mapped[str] = mapped_column(String, default="")
    how_did_you_meet_us: Mapped[str] = mapped_column(String, default="")
    groups: Mapped[List["HackerGroup"]] = relationship(
        "HackerGroup", secondary="hacker_group_user"
    )
    # is_leader: bool = mapped_column(Integer, default=0)
    events: Mapped[List["Event"]] = relationship(
        "Event", secondary="hacker_event_participation"
    )

    __mapper_args__ = {
        "polymorphic_identity": UserType.HACKER.value,
        "with_polymorphic": "*",
    }
