from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship
from src.impl.Event.model import Event, LleidaHackerParticipation
from src.impl.LleidaHackerGroup.model import LleidaHackerGroup, LleidaHackerGroupUser

from src.impl.User.model import User
from src.utils.UserType import UserType


class LleidaHacker(User):
    __tablename__ = 'lleida_hacker'
    user_id: int = Field(foreign_key='my_user.id', primary_key=True)
    role: str
    nif: str = Field(unique=True)
    student: bool = Field(default=True)
    active: bool = Field(default=True)
    github: str = Field(nullable=True)
    accepted: bool = Field(default=True)
    # rejected: bool = Column(Boolean, default=False)
    groups: list['LleidaHackerGroup'] = Relationship(link_model=LleidaHackerGroupUser)
    events: list['Event'] = relationship(link_model=LleidaHackerParticipation)

    __mapper_args__ = {
        "polymorphic_identity": UserType.LLEIDAHACKER.value,
    }