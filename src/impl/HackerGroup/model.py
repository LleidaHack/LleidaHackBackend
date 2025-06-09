from __future__ import annotations

from typing import List, TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.utils.Base.BaseModel import BaseModel

if TYPE_CHECKING:
    from src.impl.User.model import User


class HackerGroupUser(BaseModel):
    __tablename__ = "hacker_group_user"
    hacker_id: Mapped[int] = mapped_column(Integer,
                                           ForeignKey("hacker.user_id"),
                                           primary_key=True)
    group_id: Mapped[int] = mapped_column(Integer,
                                          ForeignKey("hacker_group.id"),
                                          primary_key=True)


class HackerGroup(BaseModel):
    __tablename__ = "hacker_group"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    leader_id: Mapped[int] = mapped_column(Integer,
                                           ForeignKey("hacker.user_id"))
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("event.id"))
    # event: Mapped["Event"] = relationship('Event', secondary='hacker_event')
    members: Mapped[List["User"]] = relationship(
        "User",
        secondary="hacker_group_user",
        primaryjoin="HackerGroup.id==hacker_group_user.c.group_id",
        secondaryjoin="User.id==hacker_group_user.c.hacker_id",
        uselist=True,
    )
