from __future__ import annotations
from typing import List
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base
from models.User import User

class Hacker(User):
    __tablename__ = 'hacker'
    user_id = Column(Integer, ForeignKey('llhk_user.id'), primary_key=True)
    banned: bool = Column(Integer, default=0)
    github: str = Column(String)
    linkedin: str = Column(String)
    groups: List[HackerGroup] = relationship('HackerGroupUser', secondary='hacker_group', backref='hacker')
    # is_leader: bool = Column(Integer, default=0)
    # events: List[Event] = relationship('Event', secondary='hacker_event')
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
    leader_id: int = Column(Integer, ForeignKey('hacker.user_id'), nullable=False)
    users: List[Hacker] = relationship('HackerGroupUser', secondary='hacker_group_user', backref='hacker_group')
