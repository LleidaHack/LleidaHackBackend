from __future__ import annotations
from asyncio import events
from typing import List
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base
from models.User import User
from schemas.Event import Event


class Hacker(User):
    __tablename__ = 'hacker'
    user_id = Column(Integer, ForeignKey('llhk_user.id'), primary_key=True)
    banned: bool = Column(Integer, default=0)
    github: str = Column(String)
    linkedin: str = Column(String)
    groups: List[HackerGroup] = relationship('HackerGroup',
                                             secondary='hacker_group_user')
    # is_leader: bool = Column(Integer, default=0)
    events: List[Event] = relationship('Event',
                                       secondary='hacker_event_participation')
    __mapper_args__ = {
        "polymorphic_identity": "hacker",
    }


class HackerGroupUser(Base):
    __tablename__ = 'hacker_group_user'
    hacker_id = Column(Integer, ForeignKey('hacker.user_id'), primary_key=True)
    group_id = Column(Integer, ForeignKey('hacker_group.id'), primary_key=True)


class HackerGroup(Base):
    __tablename__ = 'hacker_group'
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    description: str = Column(String)
    leader_id: int = Column(Integer,
                            ForeignKey('hacker.user_id'),
                            nullable=False)
    # event: Event = relationship('Event', secondary='hacker_event')
    members: List[Hacker] = relationship('Hacker',
                                         secondary='hacker_group_user')
