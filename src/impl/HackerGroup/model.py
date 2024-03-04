from __future__ import annotations
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.utils.database import Base


class HackerGroupUser(Base):
    __tablename__ = 'hacker_group_user'
    hacker_id = Column(Integer, ForeignKey('hacker.user_id'), primary_key=True)
    group_id = Column(Integer, ForeignKey('hacker_group.id'), primary_key=True)


class HackerGroup(Base):
    __tablename__ = 'hacker_group'
    id: int = Column(Integer, primary_key=True, index=True)
    code: str = (Column(String, unique=True, index=True))
    name: str = Column(String)
    description: str = Column(String)
    leader_id: int = Column(Integer,
                            ForeignKey('hacker.user_id'),
                            nullable=False)
    event_id = Column(Integer, ForeignKey('event.id'), nullable=False)
    # event: Event = relationship('Event', secondary='hacker_event')
    members = relationship('Hacker', secondary='hacker_group_user')
