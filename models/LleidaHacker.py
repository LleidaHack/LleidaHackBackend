from __future__ import annotations
from typing import List
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base

from models.User import User
# from models.LleidaHackerGroup import LleidaHackerGroup

class LleidaHacker(User):
    __tablename__ = 'lleida_hacker'
    user_id = Column(Integer, ForeignKey('llhk_user.id'), primary_key=True)
    role: str = Column(String)
    nif: str = Column(String)
    student: bool = Column(Integer, default=0)
    active: bool = Column(Integer, default=0)
    image: str = Column(String)
    github: str = Column(String)
    groups: List[LleidaHackerGroup] = relationship('LleidaHackerGroupUser', secondary='lleida_hacker_group', backref='lleida_hacker')

    __mapper_args__ = {
        "polymorphic_identity": "lleida_hacker",
    }

class LleidaHackerGroupUser(Base):
    __tablename__ = 'group_lleida_hacker_user'
    group_id = Column(Integer, ForeignKey('lleida_hacker_group.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('lleida_hacker.user_id'), primary_key=True)


class LleidaHackerGroup(Base):
    __tablename__ = 'lleida_hacker_group'
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    description: str = Column(String)
    leader_id: int = Column(Integer, ForeignKey('lleida_hacker.user_id'), nullable=False)
    members: List[LleidaHacker] = relationship('LleidaHacker', secondary='group_lleida_hacker_user', backref='lleida_hacker_group')

