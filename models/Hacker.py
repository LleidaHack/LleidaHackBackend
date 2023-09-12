from __future__ import annotations
from asyncio import events
from typing import List
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from database import Base
from models.User import User
from models.UserType import UserType
from schemas.Event import Event

from sqlalchemy.orm import deferred

class Hacker(User):
    __tablename__ = 'hacker'
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    banned: bool = deferred(Column(Integer, default=0))
    github: str = Column(String)
    linkedin: str = Column(String)
    cv: str = deferred(Column(String))
    is_verified: bool = Column(Boolean, default=0)
    groups = relationship('HackerGroup', secondary='hacker_group_user')
    # is_leader: bool = Column(Integer, default=0)
    events = relationship('Event', secondary='hacker_event_participation')

    __mapper_args__ = {
        "polymorphic_identity": UserType.HACKER.value,
    }


class HackerGroupUser(Base):
    __tablename__ = 'hacker_group_user'
    hacker_id = Column(Integer, ForeignKey('hacker.user_id'), primary_key=True)
    group_id = Column(Integer, ForeignKey('hacker_group.id'), primary_key=True)


class HackerGroup(Base):
    __tablename__ = 'hacker_group'
    id: int = Column(Integer, primary_key=True, index=True)
    code: str = Column(String, unique=True, index=True)
    name: str = Column(String)
    description: str = Column(String)
    leader_id: int = Column(Integer,
                            ForeignKey('hacker.user_id'),
                            nullable=False)
    event_id = Column(Integer, ForeignKey('event.id'), nullable=False)
    # event: Event = relationship('Event', secondary='hacker_event')
    members = relationship('Hacker', secondary='hacker_group_user')
