from __future__ import annotations
from typing import List, Optional
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from database import Base

from models.User import User
from models.UserType import UserType
from schemas.LleidaHacker import LleidaHackerGroup
from schemas.Event import Event

from sqlalchemy.orm import deferred
from sqlalchemy.orm import Mapped

class LleidaHacker(User):
    __tablename__ = 'lleida_hacker'
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    role: Mapped[str]= deferred(Column(String))
    nif: Mapped[str]= deferred(Column(String, unique=True))
    student: bool = Column(Boolean, default=True)
    active: bool = Column(Boolean, default=True)
    github: str = Column(String)
    accepted: Mapped[bool] = deferred(Column(Boolean, default=True))
    rejected: Mapped[bool] = deferred(Column(Boolean, default=False))
    groups = relationship('LleidaHackerGroup',
                          secondary='lleida_hacker_group_user')
    events = relationship('Event',
                          secondary='lleida_hacker_event_participation')

    __mapper_args__ = {
        "polymorphic_identity": UserType.LLEIDAHACKER.value,
    }


class LleidaHackerGroupUser(Base):
    __tablename__ = 'lleida_hacker_group_user'
    group_id = Column(Integer,
                      ForeignKey('lleida_hacker_group.id'),
                      primary_key=True)
    user_id = Column(Integer,
                     ForeignKey('lleida_hacker.user_id'),
                     primary_key=True)


class LleidaHackerGroup(Base):
    __tablename__ = 'lleida_hacker_group'
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    description: str = Column(String)
    leader_id: int = Column(Integer,
                            ForeignKey('lleida_hacker.user_id'),
                            nullable=True)
    # members: List[LleidaHacker] = relationship('LleidaHacker', secondary='group_lleida_hacker_user', backref='lleida_hacker_group')
    # members: List[LleidaHacker] = relationship('LleidaHacker', back_populates='lleida_hacker_group')
    members = relationship('LleidaHacker',
                           secondary='lleida_hacker_group_user')
